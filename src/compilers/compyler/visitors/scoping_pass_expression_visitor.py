#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from ..ast_checks.pass_base import PassBase
from .base_expression_visitor import BaseExpressionVisitor
from ..expressions.binary_expression import BinaryExpression
from ..expressions.call_expression import CallExpression
from ..expressions.expression import Expression
from ..expressions.identifier_expression import IdentifierExpression
from ..expressions.string_equal_expression import StringEqualExpression
from ..expressions.string_expression import StringExpression
from ..expressions.token_expression import TokenExpression
from ..expressions.type_cast_expression import TypeCastExpression
from ..expressions.unary_expression import UnaryExpression
from ..tokens.identifier_token import IdentifierToken
from ..utils.ast import AST


class ScopingPassExpressionVisitor(BaseExpressionVisitor[None]):
    def __init__(self, ast: AST, pass_base: PassBase[None]):
        self._ast: AST = ast
        self._pass_base: PassBase[None] = pass_base

    def visit_binary_expression(self, expression: BinaryExpression) -> None:
        # check the left and right expression of the binary expression
        self._pass_base.parse_expression(expression.left)
        self._pass_base.parse_expression(expression.right)

    def visit_call_expression(self, expression: CallExpression) -> None:
        # check that the function name (possibly nested expressions) exists
        self._pass_base.parse_expression(expression.expression)
        # check all argument expressions
        for argument in expression.arguments:
            self._pass_base.parse_expression(argument)

    def visit_identifier_expression(self, expression: IdentifierExpression) -> None:
        # check the inner expression
        self._pass_base.parse_expression(expression.inner_expression)

    def visit_string_equal_expression(self, expression: StringEqualExpression) -> None:
        # check the inner expression of the string equal expression
        self._pass_base.parse_expression(expression.inner)

    def visit_string_expression(self, expression: StringExpression) -> None:
        # parse all inner expression of the string, when they exist
        for element in expression.string_elements:
            if isinstance(element, Expression):
                self._pass_base.parse_expression(element)

    def visit_token_expression(self, expression: TokenExpression) -> None:
        # check if it is a token expression
        if type(expression.token) == IdentifierToken:
            # check that the identifier exists in the current or outer scopes
            self._pass_base.get_identifier_type(expression.token)

    def visit_type_cast_expression(self, expression: TypeCastExpression) -> None:
        # check the expression being type-casted
        self._pass_base.parse_expression(expression.expression)

    def visit_unary_expression(self, expression: UnaryExpression) -> None:
        # check the expression within the unary expression
        self._pass_base.parse_expression(expression.expression)
