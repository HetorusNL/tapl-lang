#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path
from typing import NoReturn

from compyler.errors.ast_error import AstError
from compyler.tokens.identifier_token import IdentifierToken
from compyler.tokens.token import Token
from compyler.tokens.type_token import TypeToken
from compyler.tokens.token_type import TokenType
from compyler.types.types import Types
from compyler.types.list_type import ListType
from compyler.utils.source_location import SourceLocation
from compyler.utils.stream import Stream


class TypeApplier:
    def __init__(self, filename: Path, types: Types):
        self._filename: Path = filename
        self._types: Types = types

    def apply(self, tokens: Stream[Token]) -> Stream[Token]:
        """loop through the provided token stream.
        replace the IdentifierToken that is a type with a TypeToken.
        modifies the token stream inplace, and returns a reference to the stream.
        """
        # TODO: make this pass continue to resolve all tokens and show the error(s) afterward

        # find a type IdentifierToken
        # consume the token and add a TypeToken
        # loop through the tokens to find the types
        for token in tokens.iter():
            if isinstance(token, IdentifierToken):
                # check that the identifier corresponds with a type
                if var_type := self._types.get(token.value):
                    # found the type of the IdentifierToken, construct the TypeToken
                    type_token: TypeToken = TypeToken(token.source_location, var_type)

                    # replace the IdentifierToken with a TypeToken
                    tokens.replace(1, type_token)

        # TODO: this multi-pass approach can probably be optimized
        # second pass to find and convert the list types to TypeTokens
        for token in tokens.iter():
            if token.token_type == TokenType.LIST:
                # a list should have a type token between brackets
                self.expect(tokens.iter_next(), TokenType.BRACKET_OPEN)
                element_type: Token = self.expect(tokens.iter_next(1), TokenType.TYPE)
                assert isinstance(element_type, TypeToken)
                bracket_close: Token = self.expect(tokens.iter_next(2), TokenType.BRACKET_CLOSE)

                # add (if not already existing) the list type with this element type
                list_type: ListType = self._types.add_list_type(element_type.type_)

                # construct the source_location
                source_location: SourceLocation = token.source_location + bracket_close.source_location

                # added the list type to the types, construct the TypeToken
                type_token: TypeToken = TypeToken(source_location, list_type)

                # replace the list with type token between brackets tokens with a TypeToken
                tokens.replace(4, type_token)

        return tokens

    def expect(self, token: Token, token_type: TokenType) -> Token:
        """expects the token to be of token_type, return token if match, raises AstError otherwise"""
        if token.token_type != token_type:
            self.ast_error(f"expected '{token_type}' but found {token.token_type}'!", token.source_location)
        return token

    def ast_error(self, message: str, source_location: SourceLocation) -> NoReturn:
        """constructs and raises an AstError"""
        raise AstError(message, self._filename, source_location)
