#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path
from typing import TYPE_CHECKING
import unittest

from compyler.tokenizer import Tokenizer
from compyler.types.type_resolver import TypeResolver

if TYPE_CHECKING:
    from compyler.tokens.token import Token
    from compyler.types.types import Types
    from compyler.utils.stream import Stream


class TestTypeResolver(unittest.TestCase):
    def test_example_file(self):
        # first tokenize the file to get a list of tokens
        this_folder: Path = Path(__file__).parent.resolve()
        example_file: Path = this_folder / "example_type_resolver.tim"
        tokenizer: Tokenizer = Tokenizer(example_file)
        tokens: Stream[Token] = tokenizer.tokenize()

        # run the TypeResolver to get the types from the class-lines
        type_resolver: TypeResolver = TypeResolver(tokens)
        types: Types = type_resolver.resolve()

        # check that the classes exist in the resolver
        self.assertIsNotNone(types.get("ClassName"))
        self.assertIsNotNone(types.get("OtherClass"))
        # check that the last 'class' doesn't get in the types
        self.assertIsNone(types.get("class"))
