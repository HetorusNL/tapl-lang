#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from .token_expression import TokenExpression
from ..tokens.token import Token
from ..tokens.token_type import TokenType
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

    @classmethod
    def additive_tokens(cls) -> tuple[TokenType, ...]:
        return (TokenType.PLUS, TokenType.MINUS)

    @classmethod
    def and_or_tokens(cls) -> tuple[TokenType, ...]:
        return (TokenType.AND_AND, TokenType.OR_OR)

    @classmethod
    def comparison_tokens(cls) -> tuple[TokenType, ...]:
        return (
            TokenType.EQUAL_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.NOT_EQUAL,
        )

    def has_binary_result(self) -> bool:
        return self.token.token_type in self.and_or_tokens() + self.comparison_tokens()

    @classmethod
    def multiplicative_tokens(cls) -> tuple[TokenType, ...]:
        return (TokenType.STAR, TokenType.SLASH)

    def __str__(self) -> str:
        return f"({self.left} {self.token.token_type} {self.right})"

    def __repr__(self) -> str:
        return f"<BinaryExpression: location {self.source_location}, {self.left} {self.token.token_type} {self.right}>"
