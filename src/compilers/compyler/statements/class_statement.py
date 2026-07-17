#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .function_statement import FunctionStatement
from .lifecycle_statement import LifecycleStatement
from .list_statement import ListStatement
from .statement import Statement
from .var_decl_statement import VarDeclStatement
from ..tokens.type_token import TypeToken
from ..types.class_type import ClassType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class ClassStatement(Statement):
    def __init__(self, name: TypeToken, source_location: SourceLocation):
        super().__init__(source_location)
        assert isinstance(name.type_, ClassType)
        self.name: TypeToken = name
        # store everything that can be in a class statement in the class
        self.variables: list[VarDeclStatement | ListStatement] = []
        self.functions: list[FunctionStatement] = []
        # start with a default/empty constructor and destructor
        self.constructor: LifecycleStatement | None = None
        self.destructor: LifecycleStatement | None = None

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_class_statement(self)

    @property
    def class_name(self) -> str:
        """syntactic sugar for the keyword of the type of the type token"""
        return f"{self.name}"

    @property
    def class_type(self) -> ClassType:
        """syntactic sugar for the class type inside the type token"""
        assert isinstance(self.name.type_, ClassType)
        return self.name.type_

    def __str__(self) -> str:
        return f"class {self.class_name}: ..."

    def __repr__(self) -> str:
        return f"<ClassStatement, location {self.source_location}, class {self.class_name}>"
