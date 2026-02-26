#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .statement import Statement
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class BreakStatement(Statement):
    def __init__(self, source_location: SourceLocation):
        super().__init__(source_location)

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_break_statement(self)

    def c_code(self) -> str:
        return "break;"

    def __str__(self) -> str:
        return "break"

    def __repr__(self) -> str:
        return f"<BreakStatement: location {self.source_location}>"
