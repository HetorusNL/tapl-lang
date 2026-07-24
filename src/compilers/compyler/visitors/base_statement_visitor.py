#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from ..errors.visitor_error import VisitorError
from ..statements.assignment_statement import AssignmentStatement
from ..statements.break_statement import BreakStatement
from ..statements.breakall_statement import BreakallStatement
from ..statements.class_statement import ClassStatement
from ..statements.continue_statement import ContinueStatement
from ..statements.enum_statement import EnumStatement
from ..statements.expression_statement import ExpressionStatement
from ..statements.for_loop_statement import ForLoopStatement
from ..statements.function_statement import FunctionStatement
from ..statements.if_statement import IfStatement
from ..statements.import_statement import ImportStatement
from ..statements.lifecycle_statement import LifecycleStatement
from ..statements.list_statement import ListStatement
from ..statements.module_statement import ModuleStatement
from ..statements.print_statement import PrintStatement
from ..statements.return_if_value_statement import ReturnIfValueStatement
from ..statements.return_statement import ReturnStatement
from ..statements.statement import Statement
from ..statements.var_decl_statement import VarDeclStatement


class BaseStatementVisitor[T]:
    def visit_assignment_statement(self, statement: AssignmentStatement) -> T:
        raise VisitorError(self, statement)

    def visit_break_statement(self, statement: BreakStatement) -> T:
        raise VisitorError(self, statement)

    def visit_breakall_statement(self, statement: BreakallStatement) -> T:
        raise VisitorError(self, statement)

    def visit_class_statement(self, statement: ClassStatement) -> T:
        raise VisitorError(self, statement)

    def visit_continue_statement(self, statement: ContinueStatement) -> T:
        raise VisitorError(self, statement)

    def visit_enum_statement(self, statement: EnumStatement) -> T:
        raise VisitorError(self, statement)

    def visit_expression_statement(self, statement: ExpressionStatement) -> T:
        raise VisitorError(self, statement)

    def visit_for_loop_statement(self, statement: ForLoopStatement) -> T:
        raise VisitorError(self, statement)

    def visit_function_statement(self, statement: FunctionStatement) -> T:
        raise VisitorError(self, statement)

    def visit_if_statement(self, statement: IfStatement) -> T:
        raise VisitorError(self, statement)

    def visit_import_statement(self, statement: ImportStatement) -> T:
        raise VisitorError(self, statement)

    def visit_lifecycle_statement(self, statement: LifecycleStatement) -> T:
        raise VisitorError(self, statement)

    def visit_list_statement(self, statement: ListStatement) -> T:
        raise VisitorError(self, statement)

    def visit_module_statement(self, statement: ModuleStatement) -> T:
        raise VisitorError(self, statement)

    def visit_print_statement(self, statement: PrintStatement) -> T:
        raise VisitorError(self, statement)

    def visit_return_if_value_statement(self, statement: ReturnIfValueStatement) -> T:
        raise VisitorError(self, statement)

    def visit_return_statement(self, statement: ReturnStatement) -> T:
        raise VisitorError(self, statement)

    def visit_var_decl_statement(self, statement: VarDeclStatement) -> T:
        raise VisitorError(self, statement)

    def visit_statement(self, statement: Statement) -> T:
        raise VisitorError(self, statement)
