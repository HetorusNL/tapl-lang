#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from ..expressions.string_expression import StringExpression
from .statement import Statement
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from ..utils.source_location import SourceLocation
from ..utils.utils import Utils

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class PrintStatement(Statement):
    def __init__(self, token: Token, value: Expression):
        source_location: SourceLocation = token.source_location + value.source_location
        super().__init__(source_location)
        self.line_end: str = "\\n" if token.token_type == TokenType.PRINTLN else ""
        self.value: Expression = value

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_print_statement(self)

    def c_code(self) -> str:
        # handle the special case of a stringexpression
        if isinstance(self.value, StringExpression):
            # pass the line_end on to the string expression
            self.value.line_end = self.line_end
            # print the string expression as string
            return f"printf({self.value.c_code()});"

        type_format_string: str = Utils.get_type_format_string(self.value)
        return f'printf("{type_format_string}{self.line_end}", {self.value.c_code()});'

    def __str__(self) -> str:
        return f"print({self.value.__str__()})"

    def __repr__(self) -> str:
        return f"<PrintStatement: location {self.source_location}, {self.value.__repr__()}>"
