#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .base_expression_visitor import BaseExpressionVisitor
from ..expressions.binary_expression import BinaryExpression
from ..expressions.call_expression import CallExpression
from ..expressions.expression import Expression
from ..expressions.expression_type import ExpressionType
from ..expressions.identifier_expression import IdentifierExpression
from ..expressions.string_equal_expression import StringEqualExpression
from ..expressions.string_expression import StringExpression
from ..expressions.this_expression import ThisExpression
from ..expressions.token_expression import TokenExpression
from ..expressions.type_cast_expression import TypeCastExpression
from ..expressions.unary_expression import UnaryExpression
from ..tokens.identifier_token import IdentifierToken
from ..tokens.character_token import CharacterToken
from ..tokens.identifier_token import IdentifierToken
from ..tokens.number_token import NumberToken
from ..tokens.string_chars_token import StringCharsToken
from ..tokens.token_type import TokenType
from ..types.character_type import CharacterType
from ..types.class_type import ClassType
from ..types.list_type import ListType
from ..types.numeric_type import NumericType
from ..types.type import Type
from ..utils.ast import AST
from ..utils.source_location import SourceLocation
from ..utils.utils import Utils

if TYPE_CHECKING:
    from ..ast_checks.typing_pass import TypingPass


class TypingPassExpressionVisitor(BaseExpressionVisitor[None]):
    def __init__(self, ast: AST, typing_pass: TypingPass):
        self._ast: AST = ast
        self._typing_pass: TypingPass = typing_pass

    def visit_binary_expression(self, expression: BinaryExpression) -> None:
        left: Expression = expression.left
        right: Expression = expression.right
        # check the left and right expression of the binary expression
        self._typing_pass.parse_expression(left)
        self._typing_pass.parse_expression(right)
        # TODO: when binary expression results in a bool, return bool type
        expression.type_ = self._typing_pass.check_expression_types(left, right, expression.source_location)

    def visit_call_expression(self, expression: CallExpression) -> None:
        # assert that we don't have an inner expression in the identifier expression
        assert expression.expression.inner_expression is None
        identifier_token: IdentifierToken = expression.expression.identifier_token
        if self._typing_pass.identifier_stack:
            # if there is a list on the identifier stack, we can call certain functions
            type_: Type = self._typing_pass.identifier_stack[-1]
            if isinstance(type_, ListType):
                # check the arguments
                # TODO: add type and number of arguments checking to arguments of list functions
                for argument in expression.arguments:
                    self._typing_pass.parse_expression(argument)
                if identifier_token.value in type_.callable_functions():
                    return_value_type: Type = self._ast.types[type_.callable_functions()[identifier_token.value]]
                    expression.type_ = return_value_type
                    expression.expression.type_ = return_value_type
                    return
            if isinstance(type_, ClassType):
                class_keyword: str = type_.keyword
                function_name: str = identifier_token.value
                # add the identifier stack class type to the expression
                expression.class_type = type_
                if function := self._typing_pass.class_scopes[class_keyword].scope.get_function(function_name):
                    self._typing_pass.check_function(function, expression)
                    expression.type_ = function.return_type.type_
                    expression.expression.type_ = expression.type_
                    return
            # otherwise it's not callable, add the error
            source_location: SourceLocation = identifier_token.source_location
            self._typing_pass.ast_error(
                f"identifier '{identifier_token}' of a '{type_}' is not callable!", source_location
            )
        elif function := self._typing_pass.scope_wrapper.scope.get_function(identifier_token.value):
            self._typing_pass.check_function(function, expression)
            # set the return type of the function as expression type
            expression.type_ = self._typing_pass.get_identifier_type(identifier_token)
            expression.expression.type_ = expression.type_
            return
        source_location: SourceLocation = identifier_token.source_location
        self._typing_pass.ast_error(f"identifier '{identifier_token}' is not callable!", source_location)

    def visit_identifier_expression(self, expression: IdentifierExpression) -> None:
        # TODO: implement
        with self._typing_pass.new_scope():
            type_: Type = self._typing_pass.get_identifier_type(expression.identifier_token)
            is_class: bool = isinstance(type_, ClassType)
            if is_class:
                expression.class_type = type_
            self._typing_pass.identifier_stack.append(type_)
            if isinstance(type_, ListType):
                expression.list_type = type_
            try:
                if expression.inner_expression:
                    self._typing_pass.parse_expression(expression.inner_expression)
                    expression.type_ = type_
                    return
            finally:
                self._typing_pass.identifier_stack.pop()
        expression.type_ = self._typing_pass.get_identifier_type(expression.identifier_token)

    def visit_string_equal_expression(self, expression: StringEqualExpression) -> None:
        # check the inner expression of the string equal expression
        self._typing_pass.parse_expression(expression.inner)
        expression.type_ = expression.inner.type_

    def visit_string_expression(self, expression: StringExpression) -> None:
        # parse all inner expression of the string, when they exist
        for element in expression.string_elements:
            if isinstance(element, Expression):
                self._typing_pass.parse_expression(element)
        expression.type_ = self._ast.types["string"]

    def visit_this_expression(self, expression: ThisExpression) -> None:
        self._typing_pass.parse_expression(expression.inner_expression)
        # TODO: should be class type, as it is an instance?
        expression.type_ = expression.inner_expression.type_

    def visit_token_expression(self, expression: TokenExpression) -> None:
        match expression.token:
            case CharacterToken():
                expression.type_ = self._ast.types["char"]
            case NumberToken():
                # no checking happens here so we're going to return a base type
                expression.type_ = self._ast.types["base"]
            case StringCharsToken():
                expression.type_ = self._ast.types["string"]
            case IdentifierToken():
                # TODO: handle callables differently, this now results in gcc errors
                # get the type from the identifier
                expression.type_ = self._typing_pass.get_identifier_type(expression.token)
            case _:
                match expression.token.token_type:
                    # TODO: refactor true/false to special booleans
                    case TokenType.TRUE:
                        expression.type_ = self._ast.types["base"]
                    case TokenType.FALSE:
                        expression.type_ = self._ast.types["base"]
                    case TokenType.NULL:
                        # TODO: refactor when ptr implemented
                        expression.type_ = self._ast.types["base"]
                    case _:
                        token: str = str(type(expression.token))
                        token_type: str = expression.token.token_type.value
                        message: str = f"token {token} with TokenType {token_type} not handled!"
                        assert False, f"internal compiler error, {message}"

    def visit_type_cast_expression(self, expression: TypeCastExpression) -> None:
        # get the type of the inner expression
        self._typing_pass.parse_expression(expression.expression)
        inner_type: Type = Utils.get_expression_type(expression.expression)
        cast_to_type: Type = expression.cast_to.type_
        # check that both are castable
        inner_type_castable: bool = isinstance(inner_type, (CharacterType, NumericType))
        cast_to_type_castable: bool = isinstance(cast_to_type, (CharacterType, NumericType))
        # we allow any NumericType and CharacterType to be type casted, otherwise we fail
        if inner_type_castable and cast_to_type_castable:
            expression.type_ = cast_to_type
        else:
            message: str = f"cannot type cast from '{inner_type.keyword}' to '{cast_to_type.keyword}'!"
            self._typing_pass.ast_error(message, expression.source_location)

    def visit_unary_expression(self, expression: UnaryExpression) -> None:
        # first parse the inner expression, and get its type
        self._typing_pass.parse_expression(expression.expression)
        inner_type: Type = Utils.get_expression_type(expression.expression)
        if expression.expression_type == ExpressionType.GROUPING:
            # if it's a grouping, anything goes, our type is the inner type
            expression.type_ = inner_type
        else:
            # otherwise it must be a numeric type
            if not isinstance(inner_type, NumericType):
                message: str = f"expected numeric type for unary expression '{expression.expression_type.name}'"
                message += f", found '{inner_type.keyword}'!"
                self._typing_pass.ast_error(message, expression.expression.source_location)
            expression.type_ = inner_type
            # TODO: NOT should end up with a bool type
