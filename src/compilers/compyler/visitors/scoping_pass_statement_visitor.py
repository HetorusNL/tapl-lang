#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from ..ast_checks.pass_base import PassBase
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
from ..statements.list_statement import ListStatement
from ..statements.print_statement import PrintStatement
from ..statements.return_statement import ReturnStatement
from ..statements.var_decl_statement import VarDeclStatement
from ..utils.ast import AST


class ScopingPassStatementVisitor(BaseStatementVisitor[None]):
    def __init__(self, ast: AST, pass_base: PassBase[None]):
        self._ast: AST = ast
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

    def visit_class_statement(self, statement: ClassStatement) -> None:
        pass
        # TODO: implement
        # raise NotImplementedError(f"StatementVisitor not implemented for {type(statement)}")

    def visit_continue_statement(self, statement: ContinueStatement) -> None:
        pass  # nothing to check in a ContinueStatement

    def visit_expression_statement(self, statement: ExpressionStatement) -> None:
        self._pass_base.parse_expression(statement.expression)

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

    def visit_list_statement(self, statement: ListStatement) -> None:
        # check the expression also for identifiers
        self._pass_base.add_identifier(statement.name, statement.list_type)

    def visit_print_statement(self, statement: PrintStatement) -> None:
        # check the expression also for identifiers
        self._pass_base.parse_expression(statement.value)

    def visit_return_statement(self, statement: ReturnStatement) -> None:
        # check the return value also for identifiers
        self._pass_base.parse_expression(statement.value)

    def visit_var_decl_statement(self, statement: VarDeclStatement) -> None:
        # first check the expression for identifiers
        if initial_value := statement.initial_value:
            self._pass_base.parse_expression(initial_value)
        # then add the variable declaration to the scope
        self._pass_base.add_identifier(statement.name, statement.type_token.type_)
