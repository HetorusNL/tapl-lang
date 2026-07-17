#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .token_type import TokenType
from .identifier_token import IdentifierToken
from ..utils.source_location import SourceLocation


class ThisToken(IdentifierToken):
    def __init__(self, source_location: SourceLocation, value: str):
        super().__init__(source_location, value)
        self.token_type = TokenType.THIS

    def __str__(self) -> str:
        return f"{self.value}"

    def __repr__(self) -> str:
        return f'<{self.token_type}: location {self.source_location}, "{self.value}">'
