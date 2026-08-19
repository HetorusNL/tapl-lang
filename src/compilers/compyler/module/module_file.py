#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path

from compyler.module.raw_import import RawImport
from compyler.tokens.token import Token
from compyler.utils.source_location import SourceLocation
from compyler.utils.stream import Stream


class ModuleFile:
    def __init__(
        self,
        name: str,
        source_location: SourceLocation,
        filename: Path,
        raw_imports: list[RawImport],
        tokens: Stream[Token],
    ):
        self.name: str = name
        self.source_location: SourceLocation = source_location
        self.filename: Path = filename
        self.raw_imports: list[RawImport] = raw_imports
        self.tokens: Stream[Token] = tokens
