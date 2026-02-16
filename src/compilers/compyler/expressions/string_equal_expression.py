#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path

from .expression import Expression
from ..tokens.token import Token
from ..utils.source_location import SourceLocation
from ..utils.utils import Utils


class StringEqualExpression(Expression):
    def __init__(self, inner: Expression, token: Token, filename: Path):
        source_location: SourceLocation = inner.source_location + token.source_location
        super().__init__(source_location)
        self.inner: Expression = inner
        self.token: Token = token
        self.filename: Path = filename

    def source_text(self) -> str:
        return Utils.get_source_text(self.filename, self.source_location)

    def c_code(self) -> str:
        inner_code: str = self.inner.c_code()
        token_code: str = self.token.token_type.value
        return f"{inner_code}{token_code}"

    def __str__(self) -> str:
        return f"{self.inner}{self.token.token_type.value}"

    def __repr__(self) -> str:
        return f"<StringEqualExpression: location {self.source_location}, {self.inner} {self.token.token_type}>"
