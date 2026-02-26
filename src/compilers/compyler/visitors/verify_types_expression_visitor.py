#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .base_expression_visitor import BaseExpressionVisitor
from ..expressions.binary_expression import BinaryExpression
from ..expressions.call_expression import CallExpression
from ..expressions.expression import Expression
from ..expressions.identifier_expression import IdentifierExpression
from ..expressions.string_equal_expression import StringEqualExpression
from ..expressions.string_expression import StringExpression
from ..expressions.this_expression import ThisExpression
from ..expressions.token_expression import TokenExpression
from ..expressions.type_cast_expression import TypeCastExpression
from ..expressions.unary_expression import UnaryExpression
from ..types.type import Type


class VerifyTypesExpressionVisitor(BaseExpressionVisitor[None]):
    def verify(self, expression: Expression) -> None:
        if expression.type_ == Type.unknown():
            print(f"FAILURE: {expression}.type_ == Type.unknown()")
        assert expression.type_ != Type.unknown()

    def visit_binary_expression(self, expression: BinaryExpression) -> None:
        self.verify(expression)
        expression.left.accept(self)
        expression.right.accept(self)

    def visit_call_expression(self, expression: CallExpression) -> None:
        self.verify(expression)
        expression.expression.accept(self)
        for argument in expression.arguments:
            argument.accept(self)

    def visit_identifier_expression(self, expression: IdentifierExpression) -> None:
        self.verify(expression)
        if expression.inner_expression:
            expression.inner_expression.accept(self)

    def visit_string_equal_expression(self, expression: StringEqualExpression) -> None:
        self.verify(expression)
        expression.inner.accept(self)

    def visit_string_expression(self, expression: StringExpression) -> None:
        self.verify(expression)
        for element in expression.string_elements:
            if isinstance(element, Expression):
                element.accept(self)

    def visit_this_expression(self, expression: ThisExpression) -> None:
        self.verify(expression)
        expression.inner_expression.accept(self)

    def visit_token_expression(self, expression: TokenExpression) -> None:
        self.verify(expression)

    def visit_type_cast_expression(self, expression: TypeCastExpression) -> None:
        self.verify(expression)
        expression.expression.accept(self)

    def visit_unary_expression(self, expression: UnaryExpression) -> None:
        self.verify(expression)
        expression.expression.accept(self)
