#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.tokens.identifier_token import IdentifierToken
from compyler.tokens.token import Token
from compyler.tokens.token_type import TokenType
from compyler.types.types import Types
from compyler.utils.stream import Stream
from compyler.utils.stream import StreamError


class TypeResolver:
    def __init__(self, tokens: Stream[Token]):
        self._tokens: Stream[Token] = tokens

    def resolve(self) -> Types:
        """resolve all types in the provided token stream.
        returns the builtin types and the resolved types from the tokens stream
        """
        types: Types = Types()

        # loop through the tokens to find class declarations and extract the types
        try:
            for token in self._tokens.iter():
                if token.token_type == TokenType.CLASS:
                    class_name: Token = self._tokens.iter_next()
                    if isinstance(class_name, IdentifierToken):
                        types.add_class_type(class_name.value)
                elif token.token_type == TokenType.ENUM:
                    enum_name: Token = self._tokens.iter_next()
                    if isinstance(enum_name, IdentifierToken):
                        types.add_enum_type(enum_name.value)
        except StreamError:
            # iterating past the end of the stream, invalid code: don't care
            pass

        return types
