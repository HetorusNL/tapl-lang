#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from ..tokens.type_token import TypeToken
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class TypeCastExpression(Expression):
    def __init__(self, source_location: SourceLocation, cast_to: TypeToken, expression: Expression):
        super().__init__(source_location)
        self.cast_to: TypeToken = cast_to
        self.expression: Expression = expression

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_type_cast_expression(self)

    def c_code(self) -> str:
        return f"(({self.cast_to.c_code()}){self.expression.c_code()})"

    def __str__(self) -> str:
        return f"({self.cast_to}){self.expression}"

    def __repr__(self) -> str:
        return f"<TypeCastExpression: location {self.source_location}, ({self.cast_to}){self.expression}>"
