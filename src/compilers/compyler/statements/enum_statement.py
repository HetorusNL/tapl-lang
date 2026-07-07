#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.binary_expression import BinaryExpression
from ..expressions.expression import Expression
from ..expressions.string_expression import StringExpression
from ..expressions.token_expression import TokenExpression
from .statement import Statement
from ..tokens.identifier_token import IdentifierToken
from ..tokens.number_token import NumberToken
from ..tokens.type_token import TypeToken
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from ..types.enum_type import EnumType
from ..utils.enum_entry import EnumEntry
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class EnumStatement(Statement):
    def __init__(self, name: IdentifierToken, enum_type: EnumType, source_location: SourceLocation):
        super().__init__(source_location)
        self.name: IdentifierToken = name
        self.enum_type: EnumType = enum_type
        self.type_token: TypeToken = TypeToken(name.source_location, enum_type)
        # store a list of enum entries
        self._entries: list[EnumEntry] = []
        self._prev_enum_value: Expression | None = None

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_enum_statement(self)

    def _generate_value(self, prev: Expression | None = None) -> Expression:
        if prev is None:
            return TokenExpression(self.source_location, NumberToken(self.source_location, 0))
        else:
            # increment the previous value by 1
            return BinaryExpression(
                prev,
                Token(TokenType.PLUS, self.source_location),
                TokenExpression(self.source_location, NumberToken(self.source_location, 1)),
            )

    def add_entry(self, entry_name: IdentifierToken, string_value: StringExpression, value: Expression | None) -> None:
        # if no value is provided, generate the next enum value
        if not value:
            value = self._generate_value(self._prev_enum_value)

        # construct the enum entry and add it to the list of entries
        self._entries.append(EnumEntry(entry_name, string_value, value))
        self._prev_enum_value = value

    def get_entries(self) -> list[EnumEntry]:
        return self._entries

    def __str__(self) -> str:
        return f"enum {self.enum_type}: ..."

    def __repr__(self) -> str:
        return f"<EnumStatement, location {self.source_location}, enum {self.enum_type}>"
