#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .statement import Statement
from ..tokens.identifier_token import IdentifierToken
from ..tokens.type_token import TypeToken
from ..types.list_type import ListType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class ListStatement(Statement):
    def __init__(self, type_token: TypeToken, name: IdentifierToken):
        # formulate the source location from the list statement from list till name
        source_location: SourceLocation = type_token.source_location + name.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        assert isinstance(type_token.type_, ListType)
        self.list_type: ListType = type_token.type_
        self.name: IdentifierToken = name

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_list_statement(self)

    def c_code(self) -> str:
        list_base: str = self.list_type.c_code()
        # create the list declaration
        code: str = f"{list_base} {self.name};"
        # call the constructor of the list
        code += f"{list_base}_constructor(&{self.name});"
        return code

    def __str__(self) -> str:
        return f"{self.list_type.keyword} {self.name}"

    def __repr__(self) -> str:
        return f"<ListStatement: location {self.source_location}, {self.list_type.keyword} {self.name}"
