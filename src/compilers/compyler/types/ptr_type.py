#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.types.type import Type


class PtrType(Type):
    def __init__(self, inner_type: Type):
        # create a simple type interface of this ptr type
        super().__init__(self.get_keyword(inner_type))
        # store the inner type
        self.inner_type: Type = inner_type

    def callable_functions(self) -> dict[str, str]:
        """a dictionary of callable functions returning pairs of: <name - return value keyword>"""
        return {}

    @property
    def name(self) -> str:
        inner_type_name: str = self.inner_type.name
        return f"ptr_{inner_type_name}{self.reference()}"

    @classmethod
    def get_keyword(cls, inner_type: Type) -> str:
        """creates the keyword of a ptr type based on its inner type"""
        return f"ptr[{inner_type.keyword}]"
