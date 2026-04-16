#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path


class ModularizeFolder:
    def __init__(self, name: Path, prefix: str):
        self.name: Path = name
        self.prefix: str = prefix

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ModularizeFolder):
            return False

        return self.name.samefile(other.name) and self.prefix == other.prefix
