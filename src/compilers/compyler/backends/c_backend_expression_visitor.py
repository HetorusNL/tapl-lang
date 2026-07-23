#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .c_backend_state import CBackendState
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
from ..tokens.character_token import CharacterToken
from ..tokens.identifier_token import IdentifierToken
from ..tokens.number_token import NumberToken
from ..tokens.string_chars_token import StringCharsToken
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from ..types.enum_type import EnumType
from ..types.list_type import ListType
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
        # utility functions used in this CallExpression
        def _dereference() -> str:
            assert expression.base_expression
            return f"" if expression.base_expression.type_.is_reference else f"&"

        def _get_argument_code(argument: Expression) -> str:
            if isinstance(argument, IdentifierExpression):
                if isinstance(argument.type_, ListType) and not argument.type_.is_reference:
                    return f"&{argument.identifier_token}"
            return argument.accept(self)

        def _get_receiver_code(base_expression: IdentifierExpression) -> str:
            base_expression_code: str = base_expression.accept(self)
            if isinstance(base_expression.type_, ListType) and not base_expression.type_.is_reference:
                return f"&{base_expression_code}"
            return base_expression_code

        def _get_passed_arguments() -> list[str]:
            # get the code of the arguments in the expression
            arguments_code: list[str] = []
            for argument in expression.arguments:
                arguments_code.append(_get_argument_code(argument))
            return arguments_code

        def _formulate_call(first_argument: str | None, full_name: str) -> str:
            arguments_code: list[str] = [first_argument] if first_argument else []
            arguments_code.extend(_get_passed_arguments())
            arguments_str: str = ", ".join(arguments_code)
            return f"{full_name}({arguments_str})"

        # construct the function name
        function_name: str = f"{expression.identifier_token}"

        if expression.base_expression:
            if expression.class_type:
                full_name: str = f"{expression.class_type}_{function_name}"
                # formulate the instance (pointer) and get the code of the arguments in the expression
                instance: str = f"{_dereference()}{_get_receiver_code(expression.base_expression)}"
                return _formulate_call(instance, full_name)

            if expression.base_expression.list_type:
                full_name: str = f"list_{expression.base_expression.list_type.inner_type}_{function_name}"
                # formulate the instance pointer and get the code of the arguments in the expression
                instance_pointer: str = _get_receiver_code(expression.base_expression)
                return _formulate_call(instance_pointer, full_name)

            if isinstance(expression.base_expression.type_, EnumType):
                full_name: str = f"{expression.base_expression.type_}_enum_{function_name}"
                # formulate the value from base expression and get the code of the arguments in the expression
                value: str = _get_receiver_code(expression.base_expression)
                return _formulate_call(value, full_name)

        # this should generate a function call
        return _formulate_call(None, function_name)

    def visit_enum_value_expression(self, expression: EnumValueExpression) -> str:
        full_name: str = f"{expression.type_token.name}_enum_{expression.identifier_token}"
        return full_name

    def visit_identifier_expression(self, expression: IdentifierExpression) -> str:
        # utility functions used in this IdentifierExpression
        def _join() -> str:
            if expression.base_expression and expression.base_expression.identifier_token.token_type == TokenType.THIS:
                return "->"
            return "->" if expression.type_.is_reference else "."

        if expression.base_expression:
            return f"{expression.base_expression.accept(self)}{_join()}{expression.identifier_token}"

        return f"{expression.identifier_token}"

    def visit_string_equal_expression(self, expression: StringEqualExpression) -> str:
        inner_code: str = expression.inner.accept(self)
        token_code: str = expression.token.token_type.value
        return f"{inner_code}{token_code}"

    def visit_string_expression(self, expression: StringExpression) -> str:
        # TODO: support more than only print statements
        format_string: str = ""
        arguments: list[str] = []

        # start with the string start
        format_string += '"'

        # process all elements
        def _process(elements: list[Token | Expression]) -> str:
            format_string = ""
            for element in elements:
                # check if the element is a StringEqualExpression, if so add it to the format string and arguments
                if isinstance(element, StringEqualExpression):
                    # add the source text to the format string directly
                    format_string += Utils.escape_string(element.source_text())

                    # process the inner expression
                    if isinstance(element.inner, StringExpression):
                        # a nested string expression, include the format string and arguments of the elements
                        format_string += _process(element.inner.string_elements)
                    else:
                        # some other nested expression, add the format string and arguments by means of the visitor
                        format_string += Utils.get_type_format_string(element.inner)
                        arguments.append(element.inner.accept(self))

                    # element is processed, continue to the next one
                    continue

                # check if the element is a form of an expression, if so add it to the format string and arguments
                if isinstance(element, Expression):
                    format_string += Utils.get_type_format_string(element)
                    arguments.append(element.accept(self))
                    continue

                # otherwise it's a string-related token, process it
                token: Token = element
                if token.token_type == TokenType.STRING_CHARS:
                    assert isinstance(token, StringCharsToken)
                    format_string += token.value
                elif token.token_type == TokenType.IDENTIFIER:
                    assert isinstance(token, IdentifierToken)
                    format_string += f"{token}"
                # we don't care about the other string-related tokens

            return format_string

        format_string += _process(expression.string_elements)

        # end with the string end (keeping the line_end in mind)
        format_string += expression.line_end
        format_string += '"'

        # construct the final string, consisting of comma-separated format string and the arguments
        print_string: str = ", ".join([format_string, *arguments])
        return print_string

    def visit_this_expression(self, expression: ThisExpression) -> str:
        return f"{expression}"

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
                return Utils.null_value()
            # fall back to the string representation of the token type
            case _:
                return expression.token.token_type.value

    def visit_type_cast_expression(self, expression: TypeCastExpression) -> str:
        return f"(({expression.cast_to.name}){expression.expression.accept(self)})"

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
