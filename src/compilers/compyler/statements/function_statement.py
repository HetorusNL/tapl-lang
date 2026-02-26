#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .statement import Statement
from ..tokens.identifier_token import IdentifierToken
from ..tokens.type_token import TypeToken
from ..types.class_type import ClassType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class FunctionStatement(Statement):
    def __init__(self, return_type: TypeToken, name: IdentifierToken, class_type: ClassType | None = None):
        # store the initial source location, where arguments are added later
        source_location: SourceLocation = return_type.source_location + name.source_location
        super().__init__(source_location)
        self.return_type: TypeToken = return_type
        self.name: IdentifierToken = name
        self.class_type: ClassType | None = class_type
        self.arguments: list[tuple[TypeToken, IdentifierToken]] = []
        self.statements: list[Statement] = []

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_function_statement(self)

    def add_argument(self, argument_type: TypeToken, argument_name: IdentifierToken) -> None:
        # add the source lcoation of the argument type and name
        self.source_location += argument_type.source_location + argument_name.source_location
        # add the argument to the class
        self.arguments.append((argument_type, argument_name))

    def _function_name(self) -> str:
        """return the function name, dependent on whether it's a class method or not"""
        if self.class_type:
            return f"{self.class_type}_{self.name}"
        return f"{self.name}"

    def _c_declaration_base(self) -> str:
        """returns the function declaration line, without anything after the closing paren"""
        # start with the function return type and name
        code: str = f"{self.return_type.c_code()} {self._function_name()}("

        # create a list of argument type-name pairs
        arguments: list[str] = []
        # if this is a class, also add the this pointer to the function
        if self.class_type:
            arguments.append(f"{self.class_type}* this")
        # construct the function declaration arguments from the list of arguments
        for argument_type, argument_name in self.arguments:
            arguments.append(f"{argument_type.c_code()} {argument_name}")
        # add comma separated list of the argument type-name pairs
        code += ", ".join(arguments)
        code += f")"

        return code

    def c_declaration(self) -> str:
        """returns the function declaration with terminating semicolon"""
        code: str = f"{self._c_declaration_base()};"

        return code

    def c_code(self) -> str:
        """returns declaration and body of the function"""
        code: str = f"{self._c_declaration_base()} {{\n"

        # add the statements if they exist
        for statement in self.statements:
            code += f"{statement.c_code()}\n"

        # end with the closing bracket
        code += f"}}"

        return code

    def __str__(self) -> str:
        return f"{self.return_type} {self._function_name()}: ..."

    def __repr__(self) -> str:
        string: str = f"<FunctionStatement, location {self.source_location},"
        string += f" {self.return_type} {self._function_name()}>"
        return string
