#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .type import Type
from .numeric_type_type import NumericTypeType


class NumericType(Type):
    def __init__(
        self,
        keyword: str,
        numeric_type_type: NumericTypeType,
        num_bits: int,
        syntactic_sugar: list[str] = [],
        underlying_type: str | None = None,
    ):
        super().__init__(keyword, syntactic_sugar=syntactic_sugar, underlying_type=underlying_type)
        self._promotions: list[Type] = []
        self.numeric_type_type: NumericTypeType = numeric_type_type
        self.num_bits: int = num_bits

    def add_promotions(self, *promotions: Type) -> None:
        """add promotions to which this type can promote to"""
        self._promotions.extend(promotions)

    def get_promotions(self) -> list[Type]:
        """get the list of promotions of this type"""
        return self._promotions

    def can_promote_to(self, other: Type) -> bool:
        """check if this type can be promoted (or is of same type) as other"""
        return other == self or other in self.get_promotions()
