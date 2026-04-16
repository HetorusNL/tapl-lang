#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path

from ..utils.source_location import SourceLocation


class RawImport:
    def __init__(self, name: str, filename: Path, source_location: SourceLocation):
        self.name: str = name
        self.filename: Path = filename
        self.source_location: SourceLocation = source_location
