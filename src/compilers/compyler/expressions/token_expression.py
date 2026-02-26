#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from ..tokens.character_token import CharacterToken
from ..tokens.identifier_token import IdentifierToken
from ..tokens.number_token import NumberToken
from ..tokens.string_chars_token import StringCharsToken
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class TokenExpression(Expression):
    def __init__(self, source_location: SourceLocation, token: Token):
        super().__init__(source_location)
        self.token: Token = token

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_token_expression(self)

    def c_code(self) -> str:
        match self.token.token_type:
            # handle the special cases
            case TokenType.CHARACTER:
                assert isinstance(self.token, CharacterToken)
                return f"'{self.token}'"
            case TokenType.NUMBER:
                assert isinstance(self.token, NumberToken)
                return f"{self.token}"
            case TokenType.STRING_CHARS:
                assert isinstance(self.token, StringCharsToken)
                return f'"{self.token}"'
            case TokenType.IDENTIFIER:
                assert isinstance(self.token, IdentifierToken)
                return f"{self.token}"
            case TokenType.NULL:
                # TODO: refactor to NULL when we support pointers
                return f"0"
            # fall back to the string representation of the token type
            case _:
                return self.token.token_type.value

    def __str__(self) -> str:
        return f"{self.token}"

    def __repr__(self) -> str:
        return f"<TokenExpression: location {self.source_location}, {self.token}>"
