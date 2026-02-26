#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from .expression_type import ExpressionType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class UnaryExpression(Expression):
    def __init__(self, source_location: SourceLocation, expression_type: ExpressionType, expression: Expression):
        super().__init__(source_location)
        self.expression_type: ExpressionType = expression_type
        self.expression: Expression = expression

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_unary_expression(self)

    def c_code(self) -> str:
        match self.expression_type:
            case ExpressionType.GROUPING:
                return f"({self.expression.c_code()})"
            case ExpressionType.NOT:
                return f"(!({self.expression.c_code()}))"
            case ExpressionType.MINUS:
                return f"(-({self.expression.c_code()}))"
            case ExpressionType.POST_DECREMENT:
                return f"(({self.expression.c_code()})--)"
            case ExpressionType.POST_INCREMENT:
                return f"(({self.expression.c_code()})++)"
            case ExpressionType.PRE_DECREMENT:
                return f"(--({self.expression.c_code()}))"
            case ExpressionType.PRE_INCREMENT:
                return f"(++({self.expression.c_code()}))"
        assert False, f"{self.expression_type} not in UnaryExpression!"

    def __str__(self) -> str:
        return f"({self.expression})"

    def __repr__(self) -> str:
        return f"<UnaryExpression: location {self.source_location}, {self.expression}>"
