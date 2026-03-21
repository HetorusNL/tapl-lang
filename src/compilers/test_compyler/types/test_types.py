#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

import unittest

from compyler.types.numeric_type import NumericType
from compyler.types.type import Type
from compyler.types.types import Types


class TestTypes(unittest.TestCase):
    def test_builtin_types(self):
        types: Types = Types()

        # test that the keyword and sugar objects point to same type
        self.assertEqual(types.types["u1"], types.types["bool"])

        # test that other types are different
        self.assertNotEqual(types.types["u1"], types.types["u8"])

    def test_add_existing_type(self):
        # test that adding existing type doesn't add it
        types: Types = Types()
        # extract the first keyword
        types_keys = types.types.keys()
        keyword: str = list(types_keys)[0]
        num_keys_before: int = len(types.types.keys())
        types.add(keyword)
        num_keys_after: int = len(types.types.keys())
        self.assertEqual(num_keys_before, num_keys_after)

    def test_add_new_type(self):
        # test that a new type is added, and points to the same type
        types: Types = Types()
        types.add("non_existing_type_1337")
        self.assertTrue(types.types.get("non_existing_type_1337"))

    def test_get_nonexisting_type(self):
        # test that None is returned when a type doesn't exist
        types: Types = Types()
        self.assertIsNone(types.get("non_existing_type_1337"))

    def test_get_builtin_type(self):
        # test that builtin types can also be getted
        types: Types = Types()
        self.assertIsInstance(types.get("u1"), Type)

    def test_get_added_type(self):
        # test that a type added, can be getted
        types: Types = Types()
        types.add("new_type_1337")
        self.assertIsInstance(types.get("new_type_1337"), Type)

    def test_get_promotions(self):
        # test get_promotion for unsigned/signed and floating point values
        types: Types = Types()
        u1: Type | None = types.get("u1")
        assert type(u1) == NumericType
        promotions: list[Type] = u1.get_promotions()
        self.assertIn(types.get("u8"), promotions)

        s8: Type | None = types.get("s8")
        assert type(s8) == NumericType
        promotions: list[Type] = s8.get_promotions()
        self.assertIn(types.get("s16"), promotions)

        f32: Type | None = types.get("f32")
        assert type(f32) == NumericType
        promotions: list[Type] = f32.get_promotions()
        self.assertIn(types.get("f64"), promotions)

    def test_can_promote_to(self):
        # test that a type can promote to itself or a bigger (same) type
        types: Types = Types()
        u1: Type | None = types.get("u1")
        assert type(u1) == NumericType
        u8: Type | None = types.get("u8")
        assert type(u8) == NumericType
        s8: Type | None = types.get("s8")
        assert type(s8) == NumericType
        f32: Type | None = types.get("f32")
        assert type(f32) == NumericType

        self.assertTrue(u1.can_promote_to(u1))
        self.assertTrue(u1.can_promote_to(u8))
        self.assertFalse(u1.can_promote_to(s8))
        self.assertFalse(u1.can_promote_to(f32))
