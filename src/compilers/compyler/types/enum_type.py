#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .type import Type


class EnumType(Type):
    def __init__(self, keyword: str):
        # create a simple super class for this enum type
        super().__init__(keyword)
        self.is_reference = True

    def callable_functions(self) -> dict[str, str]:
        """a dictionary of callable functions returning pairs of: <name - return value keyword>"""
        return {
            "to_string": "string",
        }
