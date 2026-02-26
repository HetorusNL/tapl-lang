#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from copy import deepcopy
from typing import TYPE_CHECKING

from ..types.type import Type
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class Expression:
    def __init__(self, source_location: SourceLocation):
        self.source_location: SourceLocation = source_location
        self._internal_type_ref_: Type = Type.unknown()

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_expression(self)

    @property
    def type_(self) -> Type:
        return self._internal_type_ref_

    @type_.setter
    def type_(self, type_: Type) -> None:
        # always store a copy of the type
        self._internal_type_ref_ = deepcopy(type_)

    def c_code(self) -> str:
        assert False, f"we can't generate code for a {type(self)}!"

    def __str__(self) -> str:
        return f""

    def __repr__(self) -> str:
        return f"<Expression: location {self.source_location}>"
