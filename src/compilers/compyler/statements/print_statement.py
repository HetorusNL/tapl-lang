#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from .statement import Statement
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from ..utils.source_location import SourceLocation

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

    def __str__(self) -> str:
        return f"print({self.value.__str__()})"

    def __repr__(self) -> str:
        return f"<PrintStatement: location {self.source_location}, {self.value.__repr__()}>"
