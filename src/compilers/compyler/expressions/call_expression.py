#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from ..expressions.identifier_expression import IdentifierExpression
from ..tokens.identifier_token import IdentifierToken
from ..types.class_type import ClassType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class CallExpression(Expression):
    def __init__(
        self,
        source_location: SourceLocation,
        expression: IdentifierExpression,
        class_type: ClassType | None,
        arguments: list[Expression] = [],
    ):
        super().__init__(source_location)
        self.expression: IdentifierExpression = expression
        self.class_type: ClassType | None = class_type
        self.arguments: list[Expression] = arguments
        self.call_consumed: bool = False

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_call_expression(self)

    def consume(self) -> IdentifierToken:
        # consume the call, as it will be generated at the outermost identifier expression
        self.call_consumed = True
        return self.expression.identifier_token

    def __str__(self) -> str:
        return f'{self.expression.__str__()}({", ".join([argument.__str__() for argument in self.arguments])})'

    def __repr__(self) -> str:
        return f"<CallExpression: location {self.source_location}, {self.expression.__repr__()}>"
