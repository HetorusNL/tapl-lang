#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from .statement import Statement
from ..tokens.token import Token

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class ReturnIfStatement(Statement):
    def __init__(self, token: Token):
        super().__init__(token.source_location)

        # store the rest of the variables in the class
        self.expressions: list[Expression] = []

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_return_if_statement(self)

    def __str__(self) -> str:
        return f"return_if({', '.join(str(expr) for expr in self.expressions)})"

    def __repr__(self) -> str:
        expressions: str = ", ".join(repr(expr) for expr in self.expressions)
        return f"<ReturnIfStatement: location {self.source_location}, expressions ({expressions})>"
