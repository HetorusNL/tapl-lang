#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .token_type import TokenType
from .identifier_token import IdentifierToken
from ..types.type import Type
from ..utils.source_location import SourceLocation


class TypeToken(IdentifierToken):
    def __init__(self, source_location: SourceLocation, type_: Type):
        super().__init__(source_location, type_.name, TokenType.TYPE)
        # store the additional properties in the class
        self.type_: Type = type_

    @property
    def name(self) -> str:
        return self.type_.name

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f'<{self.token_type}: location {self.source_location}, "{self.name}">'
