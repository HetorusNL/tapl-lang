#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.types.numeric_type import NumericType
from compyler.types.numeric_type_type import NumericTypeType
from compyler.types.type import Type


class CharacterType(Type):
    def __init__(self):
        keyword: str = "char"
        super().__init__(keyword)
        # store the inner type
        self.inner_type: NumericType = NumericType(keyword, NumericTypeType.UNSIGNED, 8, underlying_type="u8")
