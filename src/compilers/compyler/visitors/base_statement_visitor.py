#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.errors.visitor_error import VisitorError
from compyler.statements.assignment_statement import AssignmentStatement
from compyler.statements.break_statement import BreakStatement
from compyler.statements.breakall_statement import BreakallStatement
from compyler.statements.case_statement import CaseStatement
from compyler.statements.class_statement import ClassStatement
from compyler.statements.continue_statement import ContinueStatement
from compyler.statements.default_statement import DefaultStatement
from compyler.statements.enum_statement import EnumStatement
from compyler.statements.expression_statement import ExpressionStatement
from compyler.statements.fallthrough_statement import FallthroughStatement
from compyler.statements.for_loop_statement import ForLoopStatement
from compyler.statements.function_statement import FunctionStatement
from compyler.statements.if_statement import IfStatement
from compyler.statements.import_statement import ImportStatement
from compyler.statements.lifecycle_statement import LifecycleStatement
from compyler.statements.list_statement import ListStatement
from compyler.statements.module_statement import ModuleStatement
from compyler.statements.print_statement import PrintStatement
from compyler.statements.return_if_value_statement import ReturnIfValueStatement
from compyler.statements.return_statement import ReturnStatement
from compyler.statements.statement import Statement
from compyler.statements.switch_statement import SwitchStatement
from compyler.statements.var_decl_statement import VarDeclStatement


class BaseStatementVisitor[T]:
    def visit_assignment_statement(self, statement: AssignmentStatement) -> T:
        raise VisitorError(self, statement)

    def visit_break_statement(self, statement: BreakStatement) -> T:
        raise VisitorError(self, statement)

    def visit_breakall_statement(self, statement: BreakallStatement) -> T:
        raise VisitorError(self, statement)

    def visit_case_statement(self, statement: CaseStatement) -> T:
        raise VisitorError(self, statement)

    def visit_class_statement(self, statement: ClassStatement) -> T:
        raise VisitorError(self, statement)

    def visit_continue_statement(self, statement: ContinueStatement) -> T:
        raise VisitorError(self, statement)

    def visit_default_statement(self, statement: DefaultStatement) -> T:
        raise VisitorError(self, statement)

    def visit_enum_statement(self, statement: EnumStatement) -> T:
        raise VisitorError(self, statement)

    def visit_expression_statement(self, statement: ExpressionStatement) -> T:
        raise VisitorError(self, statement)

    def visit_fallthrough_statement(self, statement: FallthroughStatement) -> T:
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

    def visit_statement(self, statement: Statement) -> T:
        raise VisitorError(self, statement)

    def visit_switch_statement(self, statement: SwitchStatement) -> T:
        raise VisitorError(self, statement)

    def visit_var_decl_statement(self, statement: VarDeclStatement) -> T:
        raise VisitorError(self, statement)
