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


class ModuleStatement(Statement):
    def __init__(self, token: Token, names: list[IdentifierToken]):
        # formulate the source location from the module token and name
        source_location: SourceLocation = token.source_location
        for name in names:
            source_location += name.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        self.token: Token = token
        self.names: list[IdentifierToken] = names

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_module_statement(self)

    def __str__(self) -> str:
        module_name: str = ".".join(f"{name}" for name in self.names)
        return f"{self.token.token_type.value} {module_name}"

    def __repr__(self) -> str:
        return f"<ModuleStatement: location {self.source_location}, {self.__str__()}>"
