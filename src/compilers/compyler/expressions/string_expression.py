#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from .string_equal_expression import StringEqualExpression
from ..tokens.string_chars_token import StringCharsToken
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from ..utils.source_location import SourceLocation
from ..utils.utils import Utils

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class StringExpression(Expression):
    def __init__(self, string_start: Token):
        source_location: SourceLocation = string_start.source_location
        super().__init__(source_location)
        self.string_elements: list[Token | Expression] = [string_start]
        # the line end is updated to '\n' when it's inside a println
        self.line_end: str = ""

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_string_expression(self)

    def add_token(self, element: Token | Expression) -> None:
        self.source_location += element.source_location
        self.string_elements.append(element)

    def _raw_string(self) -> str:
        string: str = ""
        for element in self.string_elements:
            # check if the element is an expression, if so add its c_code
            if isinstance(element, Expression):
                string += element.c_code()
                continue
            # otherwise it's a string-related token, process it
            token: Token = element
            match token.token_type:
                case TokenType.STRING_START:
                    string += '"'
                case TokenType.STRING_END:
                    string += '"'
                case TokenType.STRING_CHARS:
                    assert isinstance(token, StringCharsToken)
                    string += token.value
                case TokenType.STRING_EXPR_START:
                    string += "{"
                case TokenType.STRING_EXPR_END:
                    string += "}"
                case _:
                    assert False, f"found an unknown token of type {token.token_type} in a string expression!"
        return string

    def c_code(self) -> str:
        # TODO: support more than only print statements
        format_string: str = ""
        arguments: list[str] = []

        for element in self.string_elements:
            # check if the element is a StringEqualExpression, if so add it to the format string and add the arguments
            if isinstance(element, StringEqualExpression):
                format_string += f"%s"
                format_string += Utils.get_type_format_string(element.inner)
                arguments.append(f'"{element.source_text()}"')
                arguments.append(element.inner.c_code())
                continue
            # check if the element is a form of an expression, if so add it to the format string and add the argument
            if isinstance(element, Expression):
                format_string += Utils.get_type_format_string(element)
                arguments.append(element.c_code())
                continue
            # otherwise it's a string-related token, process it
            token: Token = element
            if token.token_type == TokenType.STRING_START:
                format_string += '"'
            elif token.token_type == TokenType.STRING_END:
                format_string += self.line_end
                format_string += '"'
            elif token.token_type == TokenType.STRING_CHARS:
                assert isinstance(token, StringCharsToken)
                format_string += token.value

        print_string: str = ", ".join([format_string, *arguments])
        return print_string

    def __str__(self) -> str:
        return self._raw_string()

    def __repr__(self) -> str:
        return f"<StringExpression: location {self.source_location}, {self._raw_string()}"
