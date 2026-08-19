#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from compyler.expressions.expression import Expression
from compyler.statements.statement import Statement
from compyler.tokens.identifier_token import IdentifierToken
from compyler.tokens.type_token import TypeToken
from compyler.types.class_type import ClassType
from compyler.utils.source_location import SourceLocation

if TYPE_CHECKING:
    from compyler.visitors.base_statement_visitor import BaseStatementVisitor


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
        self.class_variable: bool = isinstance(type_token.type_, ClassType)

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_var_decl_statement(self)

    def __str__(self) -> str:
        return f"{self.type_token} {self.name}"

    def __repr__(self) -> str:
        return f"<VarDeclStatement: location {self.source_location}, {self.type_token} {self.name}"
