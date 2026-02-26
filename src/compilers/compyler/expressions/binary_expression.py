#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from .token_expression import TokenExpression
from ..tokens.token import Token
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class BinaryExpression(TokenExpression):
    def __init__(self, left: Expression, token: Token, right: Expression):
        source_location: SourceLocation = left.source_location + token.source_location + right.source_location
        super().__init__(source_location, token)
        self.left: Expression = left
        self.right: Expression = right

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_binary_expression(self)

    def c_code(self) -> str:
        left_code: str = self.left.c_code()
        token_code: str = self.token.token_type.value
        right_code: str = self.right.c_code()
        return f"({left_code} {token_code} {right_code})"

    def __str__(self) -> str:
        return f"({self.left} {self.token.token_type} {self.right})"

    def __repr__(self) -> str:
        return f"<BinaryExpression: location {self.source_location}, {self.left} {self.token.token_type} {self.right}>"
