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


class ReturnStatement(Statement):
    def __init__(self, token: Token, value: Expression | None = None):
        # formulate the source location of the return statement
        source_location: SourceLocation = token.source_location
        if value:
            source_location += value.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        self.value: Expression | None = value

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_return_statement(self)

    def c_code(self) -> str:
        if self.value:
            return f"return {self.value.c_code()};"
        else:
            return f"return;"

    def __str__(self) -> str:
        return f"return {self.value.__str__()}"

    def __repr__(self) -> str:
        return f"<ReturnStatement: location {self.source_location}, {self.value.__repr__()}>"
