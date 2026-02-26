#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .base_expression_visitor import BaseExpressionVisitor
from .base_statement_visitor import BaseStatementVisitor
from ..statements.assignment_statement import AssignmentStatement
from ..statements.break_statement import BreakStatement
from ..statements.breakall_statement import BreakallStatement
from ..statements.class_statement import ClassStatement
from ..statements.continue_statement import ContinueStatement
from ..statements.expression_statement import ExpressionStatement
from ..statements.for_loop_statement import ForLoopStatement
from ..statements.function_statement import FunctionStatement
from ..statements.if_statement import IfStatement
from ..statements.lifecycle_statement import LifecycleStatement
from ..statements.list_statement import ListStatement
from ..statements.print_statement import PrintStatement
from ..statements.return_statement import ReturnStatement
from ..statements.var_decl_statement import VarDeclStatement


class VerifyTypesStatementVisitor(BaseStatementVisitor[None]):
    def __init__(self, expression_visitor: BaseExpressionVisitor[None]):
        self._expression_visitor: BaseExpressionVisitor[None] = expression_visitor

    def visit_assignment_statement(self, statement: AssignmentStatement) -> None:
        statement.expression.accept(self._expression_visitor)
        statement.value.accept(self._expression_visitor)

    def visit_break_statement(self, statement: BreakStatement) -> None:
        pass  # nothing to check in a BreakStatement

    def visit_breakall_statement(self, statement: BreakallStatement) -> None:
        pass  # nothing to check in a BreakallStatement

    def visit_class_statement(self, statement: ClassStatement) -> None:
        if statement.constructor:
            statement.constructor.accept(self)
        if statement.destructor:
            statement.destructor.accept(self)
        for function in statement.functions:
            function.accept(self)
        for variable in statement.variables:
            variable.accept(self)

    def visit_continue_statement(self, statement: ContinueStatement) -> None:
        pass  # nothing to check in a ContinueStatement

    def visit_expression_statement(self, statement: ExpressionStatement) -> None:
        statement.expression.accept(self._expression_visitor)

    def visit_for_loop_statement(self, statement: ForLoopStatement) -> None:
        if statement.check:
            statement.check.accept(self._expression_visitor)
        if statement.init:
            statement.init.accept(self)
        if statement.loop:
            statement.loop.accept(self)
        for stm in statement.statements:
            stm.accept(self)

    def visit_function_statement(self, statement: FunctionStatement) -> None:
        for stm in statement.statements:
            stm.accept(self)

    def visit_if_statement(self, statement: IfStatement) -> None:
        for expression, stmlist in statement.else_if_statement_blocks:
            expression.accept(self._expression_visitor)
            for stm in stmlist:
                stm.accept(self)
        if statement.else_statements:
            for stm in statement.else_statements:
                stm.accept(self)
        statement.expression.accept(self._expression_visitor)
        for stm in statement.statements:
            stm.accept(self)

    def visit_lifecycle_statement(self, statement: LifecycleStatement) -> None:
        for stm in statement.statements:
            stm.accept(self)

    def visit_list_statement(self, statement: ListStatement) -> None:
        pass  # nothing to check in a ListStatement

    def visit_print_statement(self, statement: PrintStatement) -> None:
        statement.value.accept(self._expression_visitor)

    def visit_return_statement(self, statement: ReturnStatement) -> None:
        if statement.value:
            statement.value.accept(self._expression_visitor)

    def visit_var_decl_statement(self, statement: VarDeclStatement) -> None:
        if statement.initial_value:
            statement.initial_value.accept(self._expression_visitor)
