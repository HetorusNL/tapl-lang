#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from ..expressions.identifier_expression import IdentifierExpression
from ..expressions.this_expression import ThisExpression
from .statement import Statement
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class AssignmentStatement(Statement):
    @classmethod
    def is_assignment_form_token(cls, token: Token) -> bool:
        return token.token_type and token.token_type in {
            TokenType.EQUAL,
            TokenType.PLUS_EQUAL,
            TokenType.MINUS_EQUAL,
            TokenType.SLASH_EQUAL,
            TokenType.STAR_EQUAL,
        }

    def __init__(self, expression: ThisExpression | IdentifierExpression, assignment_token: Token, value: Expression):
        source_location: SourceLocation = expression.source_location + value.source_location
        super().__init__(source_location)
        self.expression: ThisExpression | IdentifierExpression = expression
        message: str = f"internal compiler error, expected assignment form token, got {assignment_token.token_type}"
        assert AssignmentStatement.is_assignment_form_token(assignment_token), message
        self.assignment_token: Token = assignment_token
        self.value: Expression = value

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_assignment_statement(self)

    def c_code(self) -> str:
        identifier: str = self.expression.c_code()
        assignment_form: str = self.assignment_token.token_type.value
        value: str = self.value.c_code()

        return f"{identifier} {assignment_form} {value};"

    def __str__(self) -> str:
        identifier: str = self.expression.__str__()
        value: str = self.value.__str__()

        return f"{identifier} = {value}"

    def __repr__(self) -> str:
        identifier: str = self.expression.__repr__()
        value: str = self.value.__repr__()

        return f"<AssignmantStatement: location {self.source_location}, {identifier} = {value}>"
