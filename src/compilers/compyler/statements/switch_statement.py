#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from compyler.expressions.expression import Expression
from compyler.statements.case_statement import CaseStatement
from compyler.statements.default_statement import DefaultStatement
from compyler.statements.statement import Statement
from compyler.tokens.token import Token
from compyler.utils.source_location import SourceLocation

if TYPE_CHECKING:
    from compyler.visitors.base_statement_visitor import BaseStatementVisitor


class SwitchStatement(Statement):
    def __init__(self, token: Token, expression: Expression):
        # formulate the source location of the token and expression
        source_location: SourceLocation = token.source_location + expression.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        self.expression: Expression = expression
        self.case_statements: list[CaseStatement | DefaultStatement] = []

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_switch_statement(self)

    def __str__(self) -> str:
        return f"switch ({self.expression.__str__()}): ..."

    def __repr__(self) -> str:
        return f"<SwitchStatement: location {self.source_location}, {self.expression.__repr__()}>"
