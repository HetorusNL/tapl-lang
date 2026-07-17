#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from ..expressions.identifier_expression import IdentifierExpression
from ..types.class_type import ClassType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class CallExpression(IdentifierExpression):
    def __init__(
        self,
        source_location: SourceLocation,
        identifier_expression: IdentifierExpression,
        class_type: ClassType | None,
        arguments: list[Expression] = [],
    ):
        super().__init__(source_location, identifier_expression.identifier_token)
        self.base_expression: IdentifierExpression | None = identifier_expression.base_expression
        self.class_type: ClassType | None = class_type
        self.arguments: list[Expression] = arguments

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_call_expression(self)

    def __str__(self) -> str:
        func: str = f"{self.identifier_token.__str__()}"
        args: str = f'({", ".join([argument.__str__() for argument in self.arguments])})'
        return f"{self._base_str()}{func}{args}"

    def __repr__(self) -> str:
        base_repr: str = self._base_repr()
        return f"<CallExpression: location {self.source_location}, {self.identifier_token.__repr__()}{base_repr}>"
