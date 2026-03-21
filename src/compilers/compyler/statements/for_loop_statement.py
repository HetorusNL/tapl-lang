#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from ..expressions.expression import Expression
from .statement import Statement
from ..tokens.token import Token
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..visitors.base_statement_visitor import BaseStatementVisitor


class ForLoopStatement(Statement):
    """class for a for-loop statement in the form of:

    for(init; check; loop) {statements}
    """

    def __init__(
        self,
        token: Token,
        breakall_label: str | None,
        init: Statement | None,
        check: Expression | None,
        loop: Statement | None,
        statements: list[Statement],
    ):
        # formulate the source location of the for loop
        source_location: SourceLocation = token.source_location
        if init:
            source_location += init.source_location
        if check:
            source_location += check.source_location
        if loop:
            source_location += loop.source_location
        for statement in statements:
            source_location += statement.source_location
        super().__init__(source_location)

        # store the rest of the variables in the class
        self.breakall_label: str | None = breakall_label
        self.init: Statement | None = init
        self.check: Expression | None = check
        self.loop: Statement | None = loop
        self.statements: list[Statement] = statements

    def accept[T](self, visitor: BaseStatementVisitor[T]) -> T:
        return visitor.visit_for_loop_statement(self)

    def __str__(self) -> str:
        return f"for ({self.init.__str__()}; {self.check.__str__()}; {self.loop.__str__()}): ..."

    def __repr__(self) -> str:
        string: str = f"<ForLoopStatement: location {self.source_location},"
        string += f" {self.init.__repr__()} {self.check.__repr__()} {self.loop.__repr__()}>"
        return string
