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

    def get_arguments(self) -> list[Expression]:
        from .call_expression import CallExpression

        # recurse if the inner expression is also an IdentifierExpression
        if isinstance(self.inner_expression, IdentifierExpression):
            return self.inner_expression.get_arguments()

        # otherwise this must be a CallExpression
        assert isinstance(self.inner_expression, CallExpression)

        # get the arguments list of the inner CallExpression
        return self.inner_expression.arguments

    def _join(self) -> str:
        return "->" if self.type_.is_reference else "."

    def dereference(self) -> str:
        return f"" if self.type_.is_reference else f"&"

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
