#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from ..expressions.identifier_expression import IdentifierExpression
from ..tokens.identifier_token import IdentifierToken
from ..types.class_type import ClassType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_expression_visitor import BaseExpressionVisitor


class CallExpression(Expression):
    def __init__(
        self,
        source_location: SourceLocation,
        expression: IdentifierExpression,
        class_type: ClassType | None,
        arguments: list[Expression] = [],
    ):
        super().__init__(source_location)
        self.expression: IdentifierExpression = expression
        self.class_type: ClassType | None = class_type
        self.arguments: list[Expression] = arguments
        self.call_consumed: bool = False

    def accept[T](self, visitor: BaseExpressionVisitor[T]) -> T:
        return visitor.visit_call_expression(self)

    def consume(self) -> IdentifierToken:
        # consume the call, as it will be generated at the outermost identifier expression
        self.call_consumed = True
        return self.expression.identifier_token

    def c_code(self) -> str:
        # construct the function name
        function_name: str = f"{self.expression.identifier_token}"

        # if the call has been consumed, return an empty string
        if self.call_consumed:
            return f""

        # otherwise this should generate a function call
        # build the argument list
        arguments: list[str] = []
        # if it's a class method call, prepend the 'this' argument
        if self.class_type:
            arguments.append("this")
        for argument in self.arguments:
            arguments.append(argument.c_code())
        arguments_string: str = ", ".join(arguments)

        # if it's a class method call, prepend the class name
        if self.class_type:
            function_name = f"{self.class_type}_{function_name}"

        # construct and return the whole function call
        return f"{function_name}({arguments_string})"

    def __str__(self) -> str:
        return f'{self.expression.__str__()}({", ".join([argument.__str__() for argument in self.arguments])})'

    def __repr__(self) -> str:
        return f"<CallExpression: location {self.source_location}, {self.expression.__repr__()}>"
