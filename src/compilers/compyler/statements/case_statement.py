#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from compyler.expressions.expression import Expression
from compyler.statements.fallthrough_statement import FallthroughStatement
from compyler.statements.statement import Statement
from compyler.tokens.token import Token
from compyler.utils.source_location import SourceLocation

if TYPE_CHECKING:
    from compyler.visitors.base_statement_visitor import BaseStatementVisitor


class CaseStatement(Statement):
    def __init__(self, token: Token, expression: Expression):
        # formulate the source location of the token and expression
        source_location: SourceLocation = token.source_location + expression.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        self.expression: Expression = expression
        self.statements: list[Statement] = []

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_case_statement(self)

    @property
    def has_fallthrough(self) -> FallthroughStatement | None:
        for statement in self.statements:
            if isinstance(statement, FallthroughStatement):
                return statement
        return None

    def __str__(self) -> str:
        return f"case {self.expression.__str__()}: ..."

    def __repr__(self) -> str:
        return f"<CaseStatement: location {self.source_location}, {self.expression.__repr__()}>"
