#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from ..errors.visitor_error import VisitorError
from ..expressions.binary_expression import BinaryExpression
from ..expressions.call_expression import CallExpression
from ..expressions.enum_value_expression import EnumValueExpression
from ..expressions.expression import Expression
from ..expressions.identifier_expression import IdentifierExpression
from ..expressions.string_equal_expression import StringEqualExpression
from ..expressions.string_expression import StringExpression
from ..expressions.this_expression import ThisExpression
from ..expressions.token_expression import TokenExpression
from ..expressions.type_cast_expression import TypeCastExpression
from ..expressions.unary_expression import UnaryExpression


class BaseExpressionVisitor[T]:
    def visit_binary_expression(self, expression: BinaryExpression) -> T:
        raise VisitorError(self, expression)

    def visit_call_expression(self, expression: CallExpression) -> T:
        raise VisitorError(self, expression)

    def visit_enum_value_expression(self, expression: EnumValueExpression) -> T:
        raise VisitorError(self, expression)

    def visit_expression(self, expression: Expression) -> T:
        raise VisitorError(self, expression)

    def visit_identifier_expression(self, expression: IdentifierExpression) -> T:
        raise VisitorError(self, expression)

    def visit_string_equal_expression(self, expression: StringEqualExpression) -> T:
        raise VisitorError(self, expression)

    def visit_string_expression(self, expression: StringExpression) -> T:
        raise VisitorError(self, expression)

    def visit_this_expression(self, expression: ThisExpression) -> T:
        raise VisitorError(self, expression)

    def visit_token_expression(self, expression: TokenExpression) -> T:
        raise VisitorError(self, expression)

    def visit_type_cast_expression(self, expression: TypeCastExpression) -> T:
        raise VisitorError(self, expression)

    def visit_unary_expression(self, expression: UnaryExpression) -> T:
        raise VisitorError(self, expression)
