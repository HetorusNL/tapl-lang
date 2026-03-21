#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .token_type import TokenType
from .token import Token
from ..types.type import Type
from ..utils.source_location import SourceLocation


class TypeToken(Token):
    def __init__(self, source_location: SourceLocation, type_: Type):
        super().__init__(TokenType.TYPE, source_location)
        # store the additional properties in the class
        self.type_: Type = type_

    @property
    def name(self) -> str:
        return self.type_.name

    def __str__(self) -> str:
        return f"{self.type_.keyword}"

    def __repr__(self) -> str:
        return f'<{self.token_type}: location {self.source_location}, "{self.type_.keyword}">'
