#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..ast_checks.scope_wrapper import ScopeWrapper
from .base_expression_visitor import BaseExpressionVisitor
from ..expressions.binary_expression import BinaryExpression
from ..expressions.call_expression import CallExpression
from ..expressions.enum_value_expression import EnumValueExpression
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
from ..types.enum_type import EnumType
from ..types.list_type import ListType
from ..types.numeric_type import NumericType
from ..types.type import Type
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..ast_checks.typing_pass import TypingPass


class TypingPassExpressionVisitor(BaseExpressionVisitor[None]):
    def __init__(self, typing_pass: TypingPass):
        self._typing_pass: TypingPass = typing_pass

    def visit_binary_expression(self, expression: BinaryExpression) -> None:
        left: Expression = expression.left
        right: Expression = expression.right
        # check the left and right expression of the binary expression
        self._typing_pass.parse_expression(left)
        self._typing_pass.parse_expression(right)
        # first check the types, if they can be used together
        expression.type_ = self._typing_pass.check_expression_types(left, right, expression.source_location)
        if expression.has_binary_result():
            # if the binary expression results in a boolean, set the type to bool
            expression.type_ = self._typing_pass.types["bool"]

    def visit_call_expression(self, expression: CallExpression) -> None:
        # first parse the base expression (if it exists)
        self._typing_pass.parse_expression(expression.base_expression)

        identifier_token: IdentifierToken = expression.identifier_token
        base_expression_type: Type | None = expression.base_expression.type_ if expression.base_expression else None
        if base_expression_type:
            # if the previous identifier is a list or class, we can call certain functions
            if isinstance(base_expression_type, ListType):
                # check the arguments
                # TODO: add type and number of arguments checking to arguments of list functions
                for argument in expression.arguments:
                    self._typing_pass.parse_expression(argument)
                if identifier_token.value in base_expression_type.callable_functions():
                    return_value_keyword = base_expression_type.callable_functions()[identifier_token.value]
                    return_value_type: Type = self._typing_pass.types[return_value_keyword]
                    expression.type_ = return_value_type
                    return

            if isinstance(base_expression_type, ClassType):
                class_keyword: str = base_expression_type.keyword
                function_name: str = identifier_token.value
                # add the identifier stack class type to the expression
                expression.class_type = base_expression_type
                if function := self._typing_pass.class_scopes[class_keyword].scope.get_function(function_name):
                    self._typing_pass.check_function(function, expression)
                    expression.type_ = function.return_type.type_
                    return

            if isinstance(base_expression_type, EnumType):
                # check that the function can be called on an enum
                if identifier_token.value in base_expression_type.callable_functions():
                    return_value_keyword = base_expression_type.callable_functions()[identifier_token.value]
                    return_value_type: Type = self._typing_pass.types[return_value_keyword]
                    expression.type_ = return_value_type
                    return

            # otherwise it's not callable, add the error
            source_location: SourceLocation = identifier_token.source_location
            message: str = f"identifier '{identifier_token}' of a '{base_expression_type}' is not callable!"
            self._typing_pass.ast_error(message, source_location)

        elif function := self._typing_pass.scope_wrapper.scope.get_function(identifier_token.value):
            self._typing_pass.check_function(function, expression)
            # set the return type of the function as expression type
            expression.type_ = self._typing_pass.get_identifier_type(identifier_token)
            return

        elif isinstance(expression.type_, ClassType):
            function_name: str = identifier_token.value
            function = self._typing_pass.scope_wrapper.scope.get_function(function_name)
            assert function
            self._typing_pass.check_function(function, expression)
            # if the expression type is a class, we can call the class name as constructor
            return

        source_location: SourceLocation = identifier_token.source_location
        self._typing_pass.ast_error(f"identifier '{identifier_token}' is not callable!", source_location)

    def visit_enum_value_expression(self, expression: EnumValueExpression) -> None:
        # check the base expression if it exists
        self._typing_pass.parse_expression(expression.base_expression)

        # check that the enum itself exists
        type_: Type = expression.type_token.type_
        if type_.keyword not in self._typing_pass.enum_scopes:
            source_location: SourceLocation = expression.type_token.source_location
            self._typing_pass.ast_error(f"enum '{type_.keyword}' is not defined!", source_location)
            return

        # check that the enum value exists in the enum scope
        enum_scope: ScopeWrapper = self._typing_pass.enum_scopes[type_.keyword]
        if not enum_scope.scope.get_identifier(expression.identifier_token.value):
            value: str = f"{expression.identifier_token}"
            message: str = f"enum value '{value}' is not defined in enum '{type_.keyword}'!"
            self._typing_pass.ast_error(message, expression.source_location)
            return

        # set the type of the enum value to the expression
        expression.type_ = type_

    def visit_identifier_expression(self, expression: IdentifierExpression) -> None:
        # first parse the base expression (if it exists)
        self._typing_pass.parse_expression(expression.base_expression)

        # then process the identifier itself
        with self._typing_pass.new_scope():
            # check if the expression does not have a type already
            has_type: bool = expression.type_ != Type.unknown()
            assert not has_type

            expression.type_ = self._typing_pass.get_identifier_type(expression.identifier_token)
            if isinstance(expression.type_, ListType):
                expression.list_type = expression.type_
            assert expression.type_

    def visit_string_equal_expression(self, expression: StringEqualExpression) -> None:
        # check the inner expression of the string equal expression
        self._typing_pass.parse_expression(expression.inner)
        expression.type_ = expression.inner.type_

    def visit_string_expression(self, expression: StringExpression) -> None:
        # parse all inner expression of the string, when they exist
        for element in expression.string_elements:
            if isinstance(element, Expression):
                self._typing_pass.parse_expression(element)
        expression.type_ = self._typing_pass.types["string"]

    def visit_this_expression(self, expression: ThisExpression) -> None:
        self._typing_pass.parse_expression(expression.base_expression)
        expression.type_.is_reference = True

    def visit_token_expression(self, expression: TokenExpression) -> None:
        match expression.token:
            case CharacterToken():
                expression.type_ = self._typing_pass.types["char"]
            case NumberToken():
                # no checking happens here so we're going to return a base type
                expression.type_ = self._typing_pass.types["base"]
            case StringCharsToken():
                expression.type_ = self._typing_pass.types["string"]
            case IdentifierToken():
                # TODO: handle callables differently, this now results in gcc errors
                # get the type from the identifier
                expression.type_ = self._typing_pass.get_identifier_type(expression.token)
            case _:
                match expression.token.token_type:
                    # TODO: refactor true/false to special booleans
                    case TokenType.TRUE:
                        expression.type_ = self._typing_pass.types["base"]
                    case TokenType.FALSE:
                        expression.type_ = self._typing_pass.types["base"]
                    case TokenType.NULL:
                        # TODO: refactor when ptr implemented
                        expression.type_ = self._typing_pass.types["base"]
                    case _:
                        token: str = str(type(expression.token))
                        token_type: str = expression.token.token_type.value
                        message: str = f"token {token} with TokenType {token_type} not handled!"
                        assert False, f"internal compiler error, {message}"

    def visit_type_cast_expression(self, expression: TypeCastExpression) -> None:
        # get the type of the inner expression
        self._typing_pass.parse_expression(expression.expression)
        inner_type: Type = expression.expression.type_
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
        inner_type: Type = expression.expression.type_
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
