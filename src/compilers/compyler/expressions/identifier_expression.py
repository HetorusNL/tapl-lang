#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from ..tokens.identifier_token import IdentifierToken
from ..types.class_type import ClassType
from ..types.list_type import ListType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class IdentifierExpression(Expression):
    def __init__(self, source_location: SourceLocation, identifier_token: IdentifierToken):
        super().__init__(source_location)
        self.identifier_token: IdentifierToken = identifier_token
        self.base_expression: IdentifierExpression | None = None
        self.class_type: ClassType | None = None
        self.list_type: ListType | None = None

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_identifier_expression(self)

    @property
    def full_expression_source_location(self) -> SourceLocation:
        # iterate through all base expressions to get the source location of the whole expression
        source_location: SourceLocation = self.source_location
        expression: IdentifierExpression | None = self.base_expression
        while expression:
            source_location += expression.source_location
            expression = expression.base_expression
        return source_location

    def _base_str(self) -> str:
        if self.base_expression:
            return f"{self.base_expression.__str__()}."
        return ""

    def _base_repr(self) -> str:
        if self.base_expression:
            return f", base: {self.base_expression.__repr__()}"
        return ""

    def __str__(self) -> str:
        return f"{self._base_str()}{self.identifier_token}"

    def __repr__(self) -> str:
        return f"<IdentifierExpression: location {self.source_location}, {self.identifier_token}{self._base_repr()}>"
