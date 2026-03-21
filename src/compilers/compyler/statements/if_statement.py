#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from .statement import Statement
from ..tokens.token import Token
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class IfStatement(Statement):
    def __init__(self, token: Token, expression: Expression, statements: list[Statement]):
        # formulate the source location of the expression and statements
        source_location: SourceLocation = token.source_location + expression.source_location
        for statement in statements:
            source_location += statement.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        self.expression: Expression = expression
        self.statements: list[Statement] = statements
        self.else_if_statement_blocks: list[tuple[Expression, list[Statement]]] = []
        self.else_statements: list[Statement] | None = None

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_if_statement(self)

    def add_else_if_statement_block(self, expression: Expression, statement_block: list[Statement]) -> None:
        self.else_if_statement_blocks.append((expression, statement_block))

    def __str__(self) -> str:
        return f"if ({self.expression.__str__()}): ..."

    def __repr__(self) -> str:
        return f"<IfStatement: location {self.source_location}, {self.expression.__repr__()}>"
