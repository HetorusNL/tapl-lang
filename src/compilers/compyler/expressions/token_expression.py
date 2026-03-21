#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from ..tokens.token import Token
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class TokenExpression(Expression):
    def __init__(self, source_location: SourceLocation, token: Token):
        super().__init__(source_location)
        self.token: Token = token

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_token_expression(self)

    def __str__(self) -> str:
        return f"{self.token}"

    def __repr__(self) -> str:
        return f"<TokenExpression: location {self.source_location}, {self.token}>"
