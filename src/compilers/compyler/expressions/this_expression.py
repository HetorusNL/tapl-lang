#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from compyler.expressions.identifier_expression import IdentifierExpression
from compyler.tokens.identifier_token import IdentifierToken
from compyler.types.class_type import ClassType
from compyler.types.type import Type
from compyler.utils.source_location import SourceLocation

if TYPE_CHECKING:
    from compyler.visitors.base_expression_visitor import BaseExpressionVisitor


class ThisExpression(IdentifierExpression):
    def __init__(self, source_location: SourceLocation, identifier_token: IdentifierToken, type_: ClassType):
        super().__init__(source_location, identifier_token)
        self.type_: Type = type_

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_this_expression(self)

    def __str__(self) -> str:
        return f"{self.identifier_token}"

    def __repr__(self) -> str:
        return f"<ThisExpression: location {self.source_location}, {self.identifier_token}>"
