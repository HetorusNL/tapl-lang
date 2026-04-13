#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .statement import Statement
from ..tokens.identifier_token import IdentifierToken
from ..tokens.token import Token
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class ImportStatement(Statement):
    def __init__(self, token: Token, names: list[IdentifierToken]):
        # formulate the source location from the import token and name
        source_location: SourceLocation = token.source_location
        for name in names:
            source_location += name.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        self.token: Token = token
        self.names: list[IdentifierToken] = names

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_import_statement(self)

    def __str__(self) -> str:
        return f"{self.token} {'.'.join(str(name) for name in self.names)}"

    def __repr__(self) -> str:
        return f"<ImportStatement: location {self.source_location}, {self.__str__()}>"
