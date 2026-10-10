#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from compyler.expressions.expression import Expression
from compyler.statements.statement import Statement
from compyler.types.array_type import ArrayType

if TYPE_CHECKING:
    from compyler.tokens.identifier_token import IdentifierToken
    from compyler.tokens.type_token import TypeToken
    from compyler.utils.source_location import SourceLocation
    from compyler.visitors.base_statement_visitor import BaseStatementVisitor


class ArrayStatement(Statement):
    def __init__(self, type_token: TypeToken, name: IdentifierToken, size: Expression):
        # formulate the source location from the array statement from array till name
        source_location: SourceLocation = type_token.source_location + name.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        assert isinstance(type_token.type_, ArrayType)
        self.array_type: ArrayType = type_token.type_
        self.name: IdentifierToken = name
        self.size: Expression = size

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_array_statement(self)

    def __str__(self) -> str:
        return f"{self.array_type.keyword} {self.name}"

    def __repr__(self) -> str:
        return f"<ArrayStatement: location {self.source_location}, {self.array_type.keyword} {self.name}>"
