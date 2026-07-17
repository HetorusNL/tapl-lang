#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .identifier_expression import IdentifierExpression
from ..tokens.identifier_token import IdentifierToken
from ..tokens.type_token import TypeToken
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class EnumValueExpression(IdentifierExpression):
    def __init__(self, source_location: SourceLocation, identifier_token: IdentifierToken):
        super().__init__(source_location, identifier_token)

    @property
    def type_token(self) -> TypeToken:
        assert self.base_expression
        assert isinstance(self.base_expression.identifier_token, TypeToken)
        return self.base_expression.identifier_token

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_enum_value_expression(self)

    def __str__(self) -> str:
        return f"{self._base_str()}{self.identifier_token}"

    def __repr__(self) -> str:
        return f"<EnumValueExpression: location {self.source_location}, {self.identifier_token}{self._base_repr()}>"
