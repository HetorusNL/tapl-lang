#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class ThisExpression(Expression):
    def __init__(self, source_location: SourceLocation, inner_expression: Expression):
        super().__init__(source_location)
        self.inner_expression: Expression = inner_expression

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_this_expression(self)

    def __str__(self) -> str:
        return f"this.{self.inner_expression}"

    def __repr__(self) -> str:
        return f"<ThisExpression: location {self.source_location}, this.{self.inner_expression}>"
