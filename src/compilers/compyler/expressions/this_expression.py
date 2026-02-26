#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .call_expression import CallExpression
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

    def c_code(self) -> str:
        # if the inner expression is a CallExpression, transform it into a function call
        if isinstance(self.inner_expression, CallExpression):
            return f"{self.inner_expression.c_code()}"
        # otherwise return a 'this' variable access on the class instance pointer
        return f"this->{self.inner_expression.c_code()}"

    def __str__(self) -> str:
        return f"this.{self.inner_expression}"

    def __repr__(self) -> str:
        return f"<ThisExpression: location {self.source_location}, this.{self.inner_expression}>"
