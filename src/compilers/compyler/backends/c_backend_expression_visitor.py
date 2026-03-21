#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .c_backend_state import CBackendState
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
from ..tokens.character_token import CharacterToken
from ..tokens.identifier_token import IdentifierToken
from ..tokens.number_token import NumberToken
from ..tokens.string_chars_token import StringCharsToken
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from ..utils.utils import Utils
from ..visitors.base_expression_visitor import BaseExpressionVisitor


class CBackendExpressionVisitor(BaseExpressionVisitor[str]):
    def __init__(self, state: CBackendState):
        self._state: CBackendState = state

    def visit_binary_expression(self, expression: BinaryExpression) -> str:
        left_code: str = expression.left.accept(self)
        token_code: str = expression.token.token_type.value
        right_code: str = expression.right.accept(self)
        return f"({left_code} {token_code} {right_code})"

    def visit_call_expression(self, expression: CallExpression) -> str:
        # construct the function name
        function_name: str = f"{expression.expression.identifier_token}"

        # if the call has been consumed, return an empty string
        if expression.call_consumed:
            return f""

        # otherwise this should generate a function call
        # build the argument list
        arguments: list[str] = []
        # if it's a class method call, prepend the 'this' argument
        if expression.class_type:
            arguments.append("this")
        for argument in expression.arguments:
            arguments.append(argument.accept(self))
        arguments_string: str = ", ".join(arguments)

        # if it's a class method call, prepend the class name
        if expression.class_type:
            function_name = f"{expression.class_type}_{function_name}"

        # construct and return the whole function call
        return f"{function_name}({arguments_string})"

    def visit_identifier_expression(self, expression: IdentifierExpression) -> str:
        # utility functions used in this IdentifierExpression
        def _join() -> str:
            return "->" if expression.type_.is_reference else "."

        def _inner_c_code() -> str:
            # only if we have an inner expression that has not been consumed, return it
            if expression.inner_expression:
                inner_code: str = expression.inner_expression.accept(self)
                if inner_code:
                    return f"{expression.identifier_token}{_join()}{expression.inner_expression.accept(self)}"

            return f"{expression.identifier_token}"

        # if this is a class, check if there is a call expression inside
        if expression.class_type:
            if name := expression.inner_function_call():
                # we need to create a function call of the outermost function
                full_name: str = f"{expression.class_type}_{name}"
                arguments: list[str] = [f"{expression.dereference()}{_inner_c_code()}", *expression.get_arguments()]
                arguments_str: str = ", ".join(arguments)
                return f"{full_name}({arguments_str})"

        # if this is a list, check if there is a call expression inside
        if expression.list_type:
            if name := expression.inner_function_call():
                # we need to create a function call of the outermost list
                full_name: str = f"list_{expression.list_type.inner_type}_{name}"
                arguments: list[str] = [f"{expression.dereference()}{_inner_c_code()}", *expression.get_arguments()]
                arguments_str: str = ", ".join(arguments)
                return f"{full_name}({arguments_str})"
            # pass the address of the list type, not by value
            return f"{expression.dereference()}{_inner_c_code()}"

        # otherwise simply return the identifier with potential inner expressions
        return _inner_c_code()

    def visit_string_equal_expression(self, expression: StringEqualExpression) -> str:
        inner_code: str = expression.inner.accept(self)
        token_code: str = expression.token.token_type.value
        return f"{inner_code}{token_code}"

    def visit_string_expression(self, expression: StringExpression) -> str:
        # TODO: support more than only print statements
        format_string: str = ""
        arguments: list[str] = []

        for element in expression.string_elements:
            # check if the element is a StringEqualExpression, if so add it to the format string and add the arguments
            if isinstance(element, StringEqualExpression):
                format_string += f"%s"
                format_string += Utils.get_type_format_string(element.inner)
                arguments.append(f'"{element.source_text()}"')
                arguments.append(element.inner.accept(self))
                continue
            # check if the element is a form of an expression, if so add it to the format string and add the argument
            if isinstance(element, Expression):
                format_string += Utils.get_type_format_string(element)
                arguments.append(element.accept(self))
                continue
            # otherwise it's a string-related token, process it
            token: Token = element
            if token.token_type == TokenType.STRING_START:
                format_string += '"'
            elif token.token_type == TokenType.STRING_END:
                format_string += expression.line_end
                format_string += '"'
            elif token.token_type == TokenType.STRING_CHARS:
                assert isinstance(token, StringCharsToken)
                format_string += token.value

        print_string: str = ", ".join([format_string, *arguments])
        return print_string

    def visit_this_expression(self, expression: ThisExpression) -> str:
        # if the inner expression is a CallExpression, transform it into a function call
        if isinstance(expression.inner_expression, CallExpression):
            return f"{expression.inner_expression.accept(self)}"
        # otherwise return a 'this' variable access on the class instance pointer
        return f"this->{expression.inner_expression.accept(self)}"

    def visit_token_expression(self, expression: TokenExpression) -> str:
        match expression.token.token_type:
            # handle the special cases
            case TokenType.CHARACTER:
                assert isinstance(expression.token, CharacterToken)
                return f"'{expression.token}'"
            case TokenType.NUMBER:
                assert isinstance(expression.token, NumberToken)
                return f"{expression.token}"
            case TokenType.STRING_CHARS:
                assert isinstance(expression.token, StringCharsToken)
                return f'"{expression.token}"'
            case TokenType.IDENTIFIER:
                assert isinstance(expression.token, IdentifierToken)
                return f"{expression.token}"
            case TokenType.NULL:
                # TODO: refactor to NULL when we support pointers
                return f"0"
            # fall back to the string representation of the token type
            case _:
                return expression.token.token_type.value

    def visit_type_cast_expression(self, expression: TypeCastExpression) -> str:
        return f"(({expression.cast_to.c_code()}){expression.expression.accept(self)})"

    def visit_unary_expression(self, expression: UnaryExpression) -> str:
        match expression.expression_type:
            case ExpressionType.GROUPING:
                return f"({expression.expression.accept(self)})"
            case ExpressionType.NOT:
                return f"(!({expression.expression.accept(self)}))"
            case ExpressionType.MINUS:
                return f"(-({expression.expression.accept(self)}))"
            case ExpressionType.POST_DECREMENT:
                return f"(({expression.expression.accept(self)})--)"
            case ExpressionType.POST_INCREMENT:
                return f"(({expression.expression.accept(self)})++)"
            case ExpressionType.PRE_DECREMENT:
                return f"(--({expression.expression.accept(self)}))"
            case ExpressionType.PRE_INCREMENT:
                return f"(++({expression.expression.accept(self)}))"
        assert False, f"{expression.expression_type} not in UnaryExpression!"
