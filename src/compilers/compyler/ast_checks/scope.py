#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.


from compyler.statements.function_statement import FunctionStatement
from compyler.types.type import Type


class Scope:
    def __init__(self, parent: Scope | None = None):
        self.parent: Scope | None = parent
        self.identifiers: dict[str, Type] = {}
        self.functions: dict[str, FunctionStatement] = {}

    @property
    def empty(self) -> bool:
        if self.parent:
            return False
        if self.identifiers:
            return False
        if self.functions:
            return False
        return True

    def add_identifier(self, name: str, type_: Type) -> None:
        self.identifiers[name] = type_

    def get_identifier(self, name: str) -> Type | None:
        if identifier := self.identifiers.get(name):
            return identifier
        if self.parent is not None:
            return self.parent.get_identifier(name)
        return None

    @property
    def all_identifiers(self) -> list[str]:
        identifiers: list[str] = list(self.identifiers.keys())
        if self.parent is not None:
            identifiers.extend(self.parent.all_identifiers)
        return identifiers

    def add_function(self, name: str, function: FunctionStatement) -> None:
        self.functions[name] = function

    def get_function(self, name: str) -> FunctionStatement | None:
        if function := self.functions.get(name):
            return function
        if self.parent is not None:
            return self.parent.get_function(name)
        return None
