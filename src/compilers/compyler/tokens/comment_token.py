#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.tokens.token import Token
from compyler.tokens.token_type import TokenType
from compyler.utils.source_location import SourceLocation


class CommentToken(Token):
    def __init__(self, token_type: TokenType, source_location: SourceLocation, value: str):
        super().__init__(token_type, source_location)
        # store the additional properties in the class
        self.value: str = value

    def __str__(self) -> str:
        return f"{self.value}"

    def __repr__(self) -> str:
        return f'<{self.token_type}: location {self.source_location} "{self.value}">'
