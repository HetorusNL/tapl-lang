#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.ast_checks.pass_base import PassBase
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
from compyler.statements.list_statement import ListStatement
from compyler.statements.module_statement import ModuleStatement
from compyler.statements.print_statement import PrintStatement
from compyler.statements.return_if_value_statement import ReturnIfValueStatement
from compyler.statements.return_statement import ReturnStatement
from compyler.statements.switch_statement import SwitchStatement
from compyler.statements.var_decl_statement import VarDeclStatement
from compyler.visitors.base_statement_visitor import BaseStatementVisitor


class ScopingPassStatementVisitor(BaseStatementVisitor[None]):
    def __init__(self, pass_base: PassBase[None]):
        self._pass_base: PassBase[None] = pass_base

    def visit_assignment_statement(self, statement: AssignmentStatement) -> None:
        # check that the this or identifier expression
        self._pass_base.parse_expression(statement.expression)
        # check the value (expression) also for identifiers
        self._pass_base.parse_expression(statement.value)

    def visit_break_statement(self, statement: BreakStatement) -> None:
        pass  # nothing to check in a BreakStatement

    def visit_breakall_statement(self, statement: BreakallStatement) -> None:
        pass  # nothing to check in a BreakallStatement

    def visit_case_statement(self, statement: CaseStatement) -> None:
        # check the case expression
        self._pass_base.parse_expression(statement.expression)
        # check all statements inside the case statement
        for body_statement in statement.statements:
            self._pass_base.parse_statement(body_statement)

    def visit_class_statement(self, statement: ClassStatement) -> None:
        pass
        # TODO: implement
        # raise NotImplementedError(f"StatementVisitor not implemented for {type(statement)}")

    def visit_continue_statement(self, statement: ContinueStatement) -> None:
        pass  # nothing to check in a ContinueStatement

    def visit_default_statement(self, statement: DefaultStatement) -> None:
        # check all statements inside the default statement
        for body_statement in statement.statements:
            self._pass_base.parse_statement(body_statement)

    def visit_enum_statement(self, statement: EnumStatement) -> None:
        # add the enum name to the surrounding scope
        self._pass_base.add_identifier(statement.name, statement.enum_type)
        # create a new scope for the enum entries
        with self._pass_base.new_scope():
            # loop through all enum entries and add them to the scope
            for entry in statement.get_entries():
                self._pass_base.add_identifier(entry.name, statement.enum_type)

    def visit_expression_statement(self, statement: ExpressionStatement) -> None:
        self._pass_base.parse_expression(statement.expression)

    def visit_fallthrough_statement(self, statement: FallthroughStatement) -> None:
        pass  # nothing to check in a FallthroughStatement

    def visit_for_loop_statement(self, statement: ForLoopStatement) -> None:
        # create a new scope for the for loop definition and body statements
        with self._pass_base.new_scope():
            # check the statements and expression that make up the for loop definition
            self._pass_base.parse_statement(statement.init)
            self._pass_base.parse_expression(statement.check)
            self._pass_base.parse_statement(statement.loop)
            # check all statements inside the body of the for loop
            for body_statement in statement.statements:
                self._pass_base.parse_statement(body_statement)

    def visit_function_statement(self, statement: FunctionStatement) -> None:
        # add the function name to the surrounding scope
        self._pass_base.add_identifier(statement.name, statement.return_type.type_)
        # create a new scope for the function arguments and body statements
        with self._pass_base.new_scope():
            # add the arguments to the newly created scope
            for type_token, identifier_token in statement.arguments:
                self._pass_base.add_identifier(identifier_token, type_token.type_)
            # check the statements inside the function
            for body_statement in statement.statements:
                self._pass_base.parse_statement(body_statement)

    def visit_if_statement(self, statement: IfStatement) -> None:
        # create a new scope for the if statement expression and body
        with self._pass_base.new_scope():
            # parse the expression and statements
            self._pass_base.parse_expression(statement.expression)
            for body_statement in statement.statements:
                self._pass_base.parse_statement(body_statement)
        # loop through all else-if blocks
        for else_if_expression, else_if_statements in statement.else_if_statement_blocks:
            # create a new scope for the else-if block expression and body
            with self._pass_base.new_scope():
                # parse the expression and statements
                self._pass_base.parse_expression(else_if_expression)
                for else_if_statement in else_if_statements:
                    self._pass_base.parse_statement(else_if_statement)
        # if there is an else block, loop through its statements
        if else_statements := statement.else_statements:
            with self._pass_base.new_scope():
                for else_statement in else_statements:
                    self._pass_base.parse_statement(else_statement)

    def visit_import_statement(self, statement: ImportStatement) -> None:
        pass  # nothing to check in an ImportStatement

    def visit_list_statement(self, statement: ListStatement) -> None:
        # check the expression also for identifiers
        self._pass_base.add_identifier(statement.name, statement.list_type)

    def visit_module_statement(self, statement: ModuleStatement) -> None:
        pass  # nothing to check in a ModuleStatement

    def visit_print_statement(self, statement: PrintStatement) -> None:
        # check the expression also for identifiers
        self._pass_base.parse_expression(statement.value)

    def visit_return_if_value_statement(self, statement: ReturnIfValueStatement) -> None:
        # check the value and inner expressions also for identifiers
        self._pass_base.parse_expression(statement.value)
        for expression in statement.expressions:
            self._pass_base.parse_expression(expression)

    def visit_return_statement(self, statement: ReturnStatement) -> None:
        # check the return value also for identifiers
        self._pass_base.parse_expression(statement.value)

    def visit_switch_statement(self, statement: SwitchStatement) -> None:
        # check the switch expression also for identifiers
        self._pass_base.parse_expression(statement.expression)
        # loop through all case and default statements
        for case_statement in statement.case_statements:
            self._pass_base.parse_statement(case_statement)

    def visit_var_decl_statement(self, statement: VarDeclStatement) -> None:
        # first check the expression for identifiers
        if initial_value := statement.initial_value:
            self._pass_base.parse_expression(initial_value)
        # then add the variable declaration to the scope
        self._pass_base.add_identifier(statement.name, statement.type_token.type_)
