#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .lifecycle_statement_type import LifecycleStatementType
from .statement import Statement
from ..tokens.identifier_token import IdentifierToken
from ..tokens.type_token import TypeToken
from ..types.type import Type
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class LifecycleStatement(Statement):
    def __init__(self, statement_type: LifecycleStatementType, type_: Type, source_location: SourceLocation):
        super().__init__(source_location)
        self.statement_type: LifecycleStatementType = statement_type
        self.type_: Type = type_
        self.arguments: list[tuple[TypeToken, IdentifierToken]] = []
        self.statements: list[Statement] = []

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_lifecycle_statement(self)

    def add_argument(self, argument_type: TypeToken, argument_name: IdentifierToken) -> None:
        # add the source lcoation of the argument type and name
        self.source_location += argument_type.source_location + argument_name.source_location
        # add the argument to the constructor
        self.arguments.append((argument_type, argument_name))

    def __str__(self) -> str:
        return f"{self.statement_type.name} {self.type_.keyword}: ..."

    def __repr__(self) -> str:
        string: str = f"<LifecycleStatement, location {self.source_location},"
        string += f" {self.statement_type.name} {self.type_.keyword}>"
        return string
