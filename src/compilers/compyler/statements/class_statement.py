#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .function_statement import FunctionStatement
from .lifecycle_statement import LifecycleStatement
from .lifecycle_statement_type import LifecycleStatementType
from .list_statement import ListStatement
from .statement import Statement
from .var_decl_statement import VarDeclStatement
from ..types.class_type import ClassType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class ClassStatement(Statement):
    def __init__(self, class_type: ClassType, source_location: SourceLocation):
        super().__init__(source_location)
        self.class_type: ClassType = class_type
        # store everything that can be in a class statement in the class
        self.variables: list[VarDeclStatement | ListStatement] = []
        self.functions: list[FunctionStatement] = []
        # start with a default/empty constructor and destructor
        self.constructor: LifecycleStatement | None = None
        self.destructor: LifecycleStatement | None = None

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_class_statement(self)

    def c_code(self) -> str:
        """returns the full class as a struct"""
        # start with the typedef
        code: str = f"typedef struct {self.class_type}_struct {self.class_type};\n"

        # add the class name
        code += f"struct {self.class_type}_struct {{\n"

        # add all variables
        for variable in self.variables:
            code += f"{variable.c_code()}"

        # end with the closing bracket
        code += f"}};\n"

        # add the constructor, or an empty constructor if there isn't any
        constructor: LifecycleStatement = self.constructor or LifecycleStatement(
            LifecycleStatementType.CONSTRUCTOR, self.class_type, self.source_location
        )
        code += f"{constructor.c_code()}\n"

        # add the destructor or an empty destructor if there isn't any
        destructor: LifecycleStatement = self.destructor or LifecycleStatement(
            LifecycleStatementType.DESTRUCTOR, self.class_type, self.source_location
        )
        code += f"{destructor.c_code()}\n"

        # add the methods to the class
        for method in self.functions:
            code += f"{method.c_code()}"

        return code

    def __str__(self) -> str:
        return f"class {self.class_type}: ..."

    def __repr__(self) -> str:
        return f"<ClassStatement, location {self.source_location}, class {self.class_type}>"
