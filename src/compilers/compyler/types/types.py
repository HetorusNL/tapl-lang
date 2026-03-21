#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from copy import deepcopy

from .character_type import CharacterType
from .class_type import ClassType
from .list_type import ListType
from .numeric_type import NumericType
from .numeric_type_type import NumericTypeType
from .type import Type


class Types:
    def __init__(self):
        self.types: dict[str, Type] = self.builtin_types()

        # make sure also the list[char] exists for the file stdlib functions
        self.add_list_type(self.types["char"])

    def builtin_types(self) -> dict[str, Type]:
        """returns the builtin types of the language as a dictionary:

        key: keyword
        value: Type
        """
        types_list: list[Type] = [
            Type("void", underlying_type="void"),
            NumericType("u1", NumericTypeType.UNSIGNED, 1, ["bool"], underlying_type="bool"),
            NumericType("u8", NumericTypeType.UNSIGNED, 8, underlying_type="uint8_t"),
            NumericType("u16", NumericTypeType.UNSIGNED, 16, underlying_type="uint16_t"),
            NumericType("u32", NumericTypeType.UNSIGNED, 32, underlying_type="uint32_t"),
            NumericType("u64", NumericTypeType.UNSIGNED, 64, underlying_type="uint64_t"),
            NumericType("s8", NumericTypeType.SIGNED, 8, underlying_type="int8_t"),
            NumericType("s16", NumericTypeType.SIGNED, 16, underlying_type="int16_t"),
            NumericType("s32", NumericTypeType.SIGNED, 32, underlying_type="int32_t"),
            NumericType("s64", NumericTypeType.SIGNED, 64, underlying_type="int64_t"),
            NumericType("f32", NumericTypeType.FLOATING_POINT, 32, underlying_type="float"),
            NumericType("f64", NumericTypeType.FLOATING_POINT, 64, underlying_type="double"),
            NumericType("base", NumericTypeType.SIGNED, 64),  # base type for non-determined integer values
            CharacterType(),
            Type("string"),
        ]
        types: dict[str, Type] = {}
        for type_ in types_list:
            for keyword in type_.all_keywords:
                assert keyword not in types
                types[keyword] = type_

        # add the promotions for the basic types
        u1: Type = types["u1"]
        assert type(u1) == NumericType
        u1.add_promotions(types["u8"], types["u16"], types["u32"], types["u64"])
        u8: Type = types["u8"]
        assert type(u8) == NumericType
        u8.add_promotions(types["u16"], types["u32"], types["u64"])
        u16: Type = types["u16"]
        assert type(u16) == NumericType
        u16.add_promotions(types["u32"], types["u64"])
        u32: Type = types["u32"]
        assert type(u32) == NumericType
        u32.add_promotions(types["u64"])
        s8: Type = types["s8"]
        assert type(s8) == NumericType
        s8.add_promotions(types["s16"], types["s32"], types["s64"])
        s16: Type = types["s16"]
        assert type(s16) == NumericType
        s16.add_promotions(types["s32"], types["s64"])
        s32: Type = types["s32"]
        assert type(s32) == NumericType
        s32.add_promotions(types["s64"])
        f32: Type = types["f32"]
        assert type(f32) == NumericType
        f32.add_promotions(types["f64"])

        return types

    def add(self, keyword: str) -> Type:
        """add a new type to the Types collection,
        does nothing when the type is already present in the collection,
        returns the existing or newly added type
        """
        # check if the type is already in the collection
        if keyword not in self.types:
            # create the Type, and add the keyword:Type to the collection
            type_ = Type(keyword)
            self.types[keyword] = type_

        # return the existing or newly created type
        return self[keyword]

    def add_class_type(self, keyword: str) -> ClassType:
        """add a new class type to the Types collection,
        does nothing when the class type is already present in the collection,
        returns the existing or newly added class type
        """
        # check if the type is already in the collection
        if keyword not in self.types:
            # create the Type, and add the keyword:Type to the collection
            type_ = ClassType(keyword)
            self.types[keyword] = type_

        # return the existing or newly created class type
        class_type: Type = self[keyword]
        assert isinstance(class_type, ClassType)
        return class_type

    def add_list_type(self, inner_type: Type) -> ListType:
        """add a new list type to the Types collection,
        does nothing when the list type is already present in the collection,
        returns the existing or newly added list type
        """
        # construct the keyword of the list type
        keyword: str = f"list[{inner_type.keyword}]"
        # check if the type is already in the collection
        if keyword not in self.types:
            # create the Type, and add the keyword:Type to the collection
            new_list_type = ListType(inner_type)
            self.types[keyword] = new_list_type

        # return the existing or newly created list type
        list_type: Type = self[keyword]
        assert isinstance(list_type, ListType)
        return list_type

    def get(self, keyword: str) -> Type | None:
        """returns the Type with the provided keyword, None if not present"""
        type_: Type | None = self.types.get(keyword)
        if type_:
            # always return a copy, as types can be modified
            type_ = deepcopy(type_)
        return type_

    def __getitem__(self, keyword: str) -> Type:
        keyword_type: Type | None = self.get(keyword)
        assert keyword_type
        return keyword_type
