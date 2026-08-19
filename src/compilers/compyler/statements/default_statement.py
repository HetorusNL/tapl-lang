#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from compyler.statements.fallthrough_statement import FallthroughStatement
from compyler.statements.statement import Statement
from compyler.tokens.token import Token

if TYPE_CHECKING:
    from compyler.visitors.base_statement_visitor import BaseStatementVisitor


class DefaultStatement(Statement):
    def __init__(self, token: Token):
        super().__init__(token.source_location)

        # store the rest of the variables in the class
        self.statements: list[Statement] = []

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_default_statement(self)

    @property
    def has_fallthrough(self) -> FallthroughStatement | None:
        for statement in self.statements:
            if isinstance(statement, FallthroughStatement):
                return statement
        return None

    def __str__(self) -> str:
        return f"default: ..."

    def __repr__(self) -> str:
        return f"<DefaultStatement: location {self.source_location}>"
