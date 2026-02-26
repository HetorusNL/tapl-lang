#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class Statement:
    def __init__(self, source_location: SourceLocation):
        self.source_location: SourceLocation = source_location

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_statement(self)

    def c_code(self) -> str:
        assert False, f"we can't generate code for a {type(self)}!"

    def __str__(self) -> str:
        return f""

    def __repr__(self) -> str:
        return f"<Statement: location {self.source_location}>"
