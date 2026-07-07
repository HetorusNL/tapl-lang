#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from .identifier_expression import IdentifierExpression
from ..tokens.type_token import TypeToken
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class EnumValueExpression(Expression):
    def __init__(self, type_token: TypeToken, identifier_expression: IdentifierExpression):
        source_location: SourceLocation = type_token.source_location + identifier_expression.source_location
        super().__init__(source_location)
        self.type_token: TypeToken = type_token
        self.identifier_expression: IdentifierExpression = identifier_expression

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_enum_value_expression(self)

    def __str__(self) -> str:
        return f"{self.type_token.type_}.{self.identifier_expression}"

    def __repr__(self) -> str:
        return f"<EnumValueExpression, enum {self.type_token.type_}, value {self.identifier_expression}>"
