#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .type import Type


class ListType(Type):
    def __init__(self, inner_type: Type):
        # create a simple type interface of this list type
        keyword: str = f"list[{inner_type.keyword}]"
        super().__init__(keyword)
        # store the inner type
        self.inner_type: Type = inner_type

    def callable_functions(self) -> dict[str, str]:
        """a dictionary of callable functions returning pairs of: <name - return value keyword>"""
        return {
            "size": "u64",
            "add": "void",
            "get": self.inner_type.keyword,
            "set": "bool",
            "del": "bool",
            "insert": "bool",
        }

    @property
    def name(self) -> str:
        inner_type_name: str = self.inner_type.name
        return f"list_{inner_type_name}{self.reference()}"
