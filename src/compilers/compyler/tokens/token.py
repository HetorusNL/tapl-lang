#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.tokens.token_type import TokenType
from compyler.utils.source_location import SourceLocation


class Token:
    def __init__(self, token_type: TokenType, source_location: SourceLocation):
        self.token_type: TokenType = token_type
        self.source_location: SourceLocation = source_location

    def __str__(self) -> str:
        return f"{self.token_type}"

    def __repr__(self) -> str:
        return f"<{self.token_type}: location {self.source_location}>"
