#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import Any
import unittest

from compyler.types.type import Type


class TestType(unittest.TestCase):
    def test_type_keyword(self):
        type_ = Type("keyword")
        self.assertEqual(type_.keyword, "keyword")
        self.list_equal(type_.syntactic_sugar, [])
        self.list_equal(type_.all_keywords, ["keyword"])

    def test_type_syntactic_sugar_single(self):
        type_ = Type("keyword", syntactic_sugar=["sugar"])
        self.assertEqual(type_.keyword, "keyword")
        self.list_equal(type_.syntactic_sugar, ["sugar"])
        self.list_equal(type_.all_keywords, ["keyword", "sugar"])

    def test_type_syntactic_sugar_multiple(self):
        type_ = Type("kw", syntactic_sugar=["sugar", "more", "third"])
        self.assertEqual(type_.keyword, "kw")
        self.list_equal(type_.syntactic_sugar, ["sugar", "more", "third"])
        self.list_equal(type_.all_keywords, ["kw", "sugar", "more", "third"])

    def test_basic_type(self):
        type1: Type = Type("test1", underlying_type="type")
        self.assertTrue(type1.is_basic_type)
        self.assertEqual(type1.underlying_type, "type")
        type2: Type = Type("test2", syntactic_sugar=["some", "sugar"])
        self.assertFalse(type2.is_basic_type)
        self.assertIsNone(type2.underlying_type)

    def list_equal(self, left: list[Any], right: list[Any]):
        self.assertListEqual(sorted(left), sorted(right))
