#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .function_statement import FunctionStatement
from ..tokens.identifier_token import IdentifierToken
from ..tokens.type_token import TypeToken
from ..types.class_type import ClassType


class ConstructorFunctionStatement(FunctionStatement):
    def __init__(self, return_type: TypeToken, name: IdentifierToken, class_type: ClassType | None = None):
        super().__init__(return_type, name, class_type)

    def function_name(self) -> str:
        """the function name of a constructor is always just the (class) name"""
        return f"{self.name}"
