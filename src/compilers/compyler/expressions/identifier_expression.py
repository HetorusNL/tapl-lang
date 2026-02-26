#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .expression import Expression
from ..tokens.identifier_token import IdentifierToken
from ..types.class_type import ClassType
from ..types.list_type import ListType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class IdentifierExpression(Expression):
    def __init__(self, source_location: SourceLocation, identifier_token: IdentifierToken):
        super().__init__(source_location)
        self.identifier_token: IdentifierToken = identifier_token
        self.inner_expression: Expression | None = None
        self.class_type: ClassType | None = None
        self.list_type: ListType | None = None

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_identifier_expression(self)

    def inner_function_call(self) -> IdentifierToken | None:
        from .call_expression import CallExpression

        # if there's no inner expression, there's obviously not a call
        if not self.inner_expression:
            return None

        # recurse if the inner expression is also an IdentifierExpression
        if isinstance(self.inner_expression, IdentifierExpression):
            return self.inner_expression.inner_function_call()

        # otherwise return the identifier if the inner expression is a CallExpression
        if isinstance(self.inner_expression, CallExpression):
            # consume the inner call expression
            return self.inner_expression.consume()
        else:
            return None

    def get_arguments(self) -> list[str]:
        from .call_expression import CallExpression

        # recurse if the inner expression is also an IdentifierExpression
        if isinstance(self.inner_expression, IdentifierExpression):
            return self.inner_expression.get_arguments()

        # otherwise this must be a CallExpression
        assert isinstance(self.inner_expression, CallExpression)

        # otherwise get the arguments list if the inner expression is a CallExpression
        arguments: list[str] = []
        for argument in self.inner_expression.arguments:
            arguments.append(argument.c_code())

        # add the arguments
        return arguments

    def _join(self) -> str:
        return "->" if self.type_.is_reference else "."

    def _inner_c_code(self) -> str:
        # only if we have an inner expression that has not been consumed, return it
        if self.inner_expression:
            inner_code: str = self.inner_expression.c_code()
            if inner_code:
                return f"{self.identifier_token}{self._join()}{self.inner_expression.c_code()}"

        return f"{self.identifier_token}"

    def dereference(self) -> str:
        return f"" if self.type_.is_reference else f"&"

    def c_code(self) -> str:
        # if this is a class, check if there is a call expression inside
        if self.class_type:
            if name := self.inner_function_call():
                # we need to create a function call of the outermost function
                full_name: str = f"{self.class_type}_{name}"
                arguments: str = ", ".join([f"{self.dereference()}{self._inner_c_code()}", *self.get_arguments()])
                return f"{full_name}({arguments})"

        # if this is a list, check if there is a call expression inside
        if self.list_type:
            if name := self.inner_function_call():
                # we need to create a function call of the outermost list
                full_name: str = f"list_{self.list_type.inner_type}_{name}"
                arguments: str = ", ".join([f"{self.dereference()}{self._inner_c_code()}", *self.get_arguments()])
                return f"{full_name}({arguments})"
            # pass the address of the list type, not by value
            return f"{self.dereference()}{self._inner_c_code()}"

        # otherwise simply return the identifier with potential inner expressions
        return self._inner_c_code()

    def __str__(self) -> str:
        if self.inner_expression:
            return f"{self.identifier_token}.{self.inner_expression}"
        else:
            return f"{self.identifier_token}"

    def __repr__(self) -> str:
        string: str = f"<IdentifierExpression: location {self.source_location}, {self.identifier_token}"
        if self.inner_expression:
            string = f"{string}{self._join()}{self.inner_expression}"
        string = f"{string}>"
        return string
