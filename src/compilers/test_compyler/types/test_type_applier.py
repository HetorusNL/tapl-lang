#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path
import unittest

from compyler.tokenizer import Tokenizer
from compyler.tokens.identifier_token import IdentifierToken
from compyler.tokens.token import Token
from compyler.tokens.type_token import TypeToken
from compyler.types.type_applier import TypeApplier
from compyler.types.type_resolver import TypeResolver
from compyler.types.types import Types
from compyler.utils.stream import Stream


class TestTypeApplier(unittest.TestCase):
    def test_example_file(self):
        # first tokenize the file to get a list of tokens
        this_folder: Path = Path(__file__).parent.resolve()
        example_file: Path = this_folder / "example_type_applier.tim"
        tokenizer: Tokenizer = Tokenizer(example_file)
        tokens: Stream[Token] = tokenizer.tokenize()

        # then run the TypeResolver to get the custom types
        type_resolver: TypeResolver = TypeResolver(tokens)
        types: Types = type_resolver.resolve()

        # run the TypeApplier to create the TypeToken tokens
        type_applier: TypeApplier = TypeApplier(example_file, types)
        tokens = type_applier.apply(tokens)

        # extract the variable TypeToken tokens and keywords
        type_tokens: list[TypeToken] = [token for token in tokens.objects if isinstance(token, TypeToken)]
        type_token_keywords: list[str] = []
        for token in type_tokens:
            type_token_keywords.extend(token.type_.all_keywords)

        # check that all TypeToken tokens have been created
        self.assertIn("u8", type_token_keywords)
        self.assertIn("string", type_token_keywords)
        self.assertIn("bool", type_token_keywords)
        self.assertIn("ClassName", type_token_keywords)
        self.assertIn("OtherClass", type_token_keywords)

        # extract the identifier tokens and their names
        identifier_tokens: list[IdentifierToken] = [token for token in tokens.objects if type(token) is IdentifierToken]
        identifier_values: list[str] = [token.value for token in identifier_tokens]

        # check that the type identifiers no longer exist in the token stream
        self.assertNotIn("u8", identifier_values)
        self.assertNotIn("string", identifier_values)
        self.assertNotIn("bool", identifier_values)
        # ClassName and OtherClass also exist in the declarations, so don't check
