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

    def c_code(self) -> str:
        """returns the declaration and body of the lifecycle statement"""
        code: str = f""

        # add the declaration
        match self.statement_type:
            case LifecycleStatementType.CONSTRUCTOR:
                code += f"void {self.type_.c_code()}_constructor("
            case LifecycleStatementType.DESTRUCTOR:
                code += f"void {self.type_.c_code()}_destructor("

        # create a list of argument type-name pairs, start with the pointer to the instance
        arguments: list[str] = [f"{self.type_.c_code()}* this"]
        for argument_type, argument_name in self.arguments:
            arguments.append(f"{argument_type.type_.c_code()} {argument_name}")
        # add the arguments
        code += ", ".join(arguments)

        # add the closing parenthesis and opening bracket
        code += f"){{"

        # add the statements in the lifecycle statement
        for statement in self.statements:
            code += f"{statement.c_code()}\n"

        # end with the closing bracket
        code += f"}}"

        return code

    def __str__(self) -> str:
        return f"{self.statement_type.name} {self.type_.keyword}: ..."

    def __repr__(self) -> str:
        string: str = f"<LifecycleStatement, location {self.source_location},"
        string += f" {self.statement_type.name} {self.type_.keyword}>"
        return string
