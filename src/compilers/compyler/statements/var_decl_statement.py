#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from .statement import Statement
from ..tokens.identifier_token import IdentifierToken
from ..tokens.type_token import TypeToken
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class VarDeclStatement(Statement):
    def __init__(self, type_token: TypeToken, name: IdentifierToken, initial_value: Expression | None = None):
        # formulate the source location from the type name and initial value, if passed
        source_location: SourceLocation = type_token.source_location + name.source_location
        if initial_value:
            source_location += initial_value.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        self.type_token: TypeToken = type_token
        self.name: IdentifierToken = name
        self.initial_value: Expression | None = initial_value

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_var_decl_statement(self)

    def c_code(self) -> str:
        # if we have an initial value, also generate code for that
        if self.initial_value:
            initial_value: str = self.initial_value.c_code()
            return f"{self.type_token.c_code()} {self.name} = {initial_value};"

        # otherwise it's a default initialized variable
        return f"{self.type_token} {self.name};"

    def __str__(self) -> str:
        return f"{self.type_token} {self.name}"

    def __repr__(self) -> str:
        return f"<VarDeclStatement: location {self.source_location}, {self.type_token} {self.name}"
