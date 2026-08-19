#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.expressions.binary_expression import BinaryExpression
from compyler.expressions.call_expression import CallExpression
from compyler.expressions.enum_value_expression import EnumValueExpression
from compyler.expressions.expression import Expression
from compyler.expressions.identifier_expression import IdentifierExpression
from compyler.expressions.string_equal_expression import StringEqualExpression
from compyler.expressions.string_expression import StringExpression
from compyler.expressions.this_expression import ThisExpression
from compyler.expressions.token_expression import TokenExpression
from compyler.expressions.type_cast_expression import TypeCastExpression
from compyler.expressions.unary_expression import UnaryExpression
from compyler.types.type import Type
from compyler.visitors.base_expression_visitor import BaseExpressionVisitor


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
        # process the internal IdentifierExpression
        self.visit_identifier_expression(expression)
        # process the CallExpression specifics
        for argument in expression.arguments:
            argument.accept(self)

    def visit_enum_value_expression(self, expression: EnumValueExpression) -> None:
        # process the internal IdentifierExpression
        self.visit_identifier_expression(expression)
        # nothing specific to do for the EnumValueExpression

    def visit_identifier_expression(self, expression: IdentifierExpression) -> None:
        if expression.base_expression:
            expression.base_expression.accept(self)
        self.verify(expression)

    def visit_string_equal_expression(self, expression: StringEqualExpression) -> None:
        self.verify(expression)
        expression.inner.accept(self)

    def visit_string_expression(self, expression: StringExpression) -> None:
        self.verify(expression)
        for element in expression.string_elements:
            if isinstance(element, Expression):
                element.accept(self)

    def visit_this_expression(self, expression: ThisExpression) -> None:
        # process the internal IdentifierExpression
        self.visit_identifier_expression(expression)
        # nothing specific to do for the ThisExpression

    def visit_token_expression(self, expression: TokenExpression) -> None:
        self.verify(expression)

    def visit_type_cast_expression(self, expression: TypeCastExpression) -> None:
        self.verify(expression)
        expression.expression.accept(self)

    def visit_unary_expression(self, expression: UnaryExpression) -> None:
        self.verify(expression)
        expression.expression.accept(self)
