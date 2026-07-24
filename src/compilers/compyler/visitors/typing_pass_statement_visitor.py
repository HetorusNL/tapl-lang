#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from typing import TYPE_CHECKING

from .base_statement_visitor import BaseStatementVisitor
from ..statements.assignment_statement import AssignmentStatement
from ..statements.break_statement import BreakStatement
from ..statements.breakall_statement import BreakallStatement
from ..statements.class_statement import ClassStatement
from ..statements.constructor_function_statement import ConstructorFunctionStatement
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
from ..statements.var_decl_statement import VarDeclStatement
from ..types.type import Type
from ..utils.source_location import SourceLocation

if TYPE_CHECKING:
    from ..ast_checks.typing_pass import TypingPass


class TypingPassStatementVisitor(BaseStatementVisitor[None]):
    def __init__(self, typing_pass: TypingPass):
        self._typing_pass: TypingPass = typing_pass

    def visit_assignment_statement(self, statement: AssignmentStatement) -> None:
        # get the identifier token type
        self._typing_pass.parse_expression(statement.expression)
        # check that the expression is of this type
        self._typing_pass.parse_expression(statement.value)
        # check that returned type and requested are valid
        self._typing_pass.check_expression_types(statement.expression, statement.value, statement.value.source_location)

    def visit_break_statement(self, statement: BreakStatement) -> None:
        pass  # nothing to check in a BreakStatement

    def visit_breakall_statement(self, statement: BreakallStatement) -> None:
        pass  # nothing to check in a BreakallStatement

    def visit_class_statement(self, statement: ClassStatement) -> None:
        with self._typing_pass.clean_scope() as class_scope:
            self._typing_pass.class_scopes[statement.class_name] = class_scope
            # add the stdlib functions to the class scope
            self._typing_pass.add_stdlib_functions()
            # parse the variables in the class
            for variable in statement.variables:
                self._typing_pass.parse_statement(variable)
            # parse the statements in the lifecycle functions
            if statement.constructor:
                self._typing_pass.parse_statement(statement.constructor)
            if statement.destructor:
                self._typing_pass.parse_statement(statement.destructor)
            for function in statement.functions:
                # TODO: fix assert that happens when using undeclared variables in functions
                self._typing_pass.parse_statement(function)

        # add the constructor to the surrounding scope, so it can be called like a function
        self._typing_pass.add_identifier(statement.name, statement.class_type)

        # construct the function statement for the class constructor
        constructor_function: ConstructorFunctionStatement = ConstructorFunctionStatement(
            return_type=statement.name,
            name=statement.name,
            class_type=statement.class_type,
        )
        if statement.constructor:
            # add the constructor arguments in case we have a constructor and arguments
            constructor_function.add_arguments(statement.constructor.arguments)
        self._typing_pass.scope_wrapper.scope.add_function(constructor_function.name.value, constructor_function)

    def visit_continue_statement(self, statement: ContinueStatement) -> None:
        pass  # nothing to check in a ContinueStatement

    def visit_enum_statement(self, statement: EnumStatement) -> None:
        # add the enum name to the surrounding scope
        self._typing_pass.add_identifier(statement.name, statement.enum_type)
        # create a new scope for the enum entries
        with self._typing_pass.clean_scope() as enum_scope:
            self._typing_pass.enum_scopes[statement.enum_type.keyword] = enum_scope
            # loop through all enum entries and add them to the enum scope
            for entry in statement.get_entries():
                self._typing_pass.add_identifier(entry.name, statement.enum_type)
                self._typing_pass.parse_expression(entry.string_value)
                self._typing_pass.parse_expression(entry.value)

    def visit_expression_statement(self, statement: ExpressionStatement) -> None:
        # check the expression
        self._typing_pass.parse_expression(statement.expression)

    def visit_for_loop_statement(self, statement: ForLoopStatement) -> None:
        # create a new scope for the for loop definition and body statements
        with self._typing_pass.new_scope():
            # check the statements and expression that make up the for loop definition
            self._typing_pass.parse_statement(statement.init)
            if statement.check:
                self._typing_pass.parse_expression(statement.check)
            if statement.loop:
                self._typing_pass.parse_statement(statement.loop)
            # check all statements inside the body of the for loop
            for body_statement in statement.statements:
                self._typing_pass.parse_statement(body_statement)

    def visit_function_statement(self, statement: FunctionStatement) -> None:
        # add the function name to the surrounding scope
        self._typing_pass.add_identifier(statement.name, statement.return_type.type_)
        # add the function statement also to the scope
        self._typing_pass.scope_wrapper.scope.add_function(statement.name.value, statement)
        # create a new scope for the function arguments and body statements
        with self._typing_pass.new_scope():
            # add the return type to the function return type stack
            self._typing_pass.function_stack.append(statement.return_type.type_)
            try:
                # add the arguments to the newly created scope
                for type_token, identifier_token in statement.arguments:
                    # set the type to be a reference
                    type_token.type_.is_reference = True
                    # add the argument to the scope
                    self._typing_pass.add_identifier(identifier_token, type_token.type_)
                # check the statements inside the function
                for body_statement in statement.statements:
                    self._typing_pass.parse_statement(body_statement)
            finally:
                self._typing_pass.function_stack.pop()

    def visit_if_statement(self, statement: IfStatement) -> None:
        # pretty nice, this parsing is the same as the scoping pass :)
        # create a new scope for the if statement expression and body
        with self._typing_pass.new_scope():
            # parse the expression and statements
            self._typing_pass.parse_expression(statement.expression)
            for body_statement in statement.statements:
                self._typing_pass.parse_statement(body_statement)
        # loop through all else-if blocks
        for else_if_expression, else_if_statements in statement.else_if_statement_blocks:
            # create a new scope for the else-if block expression and body
            with self._typing_pass.new_scope():
                # parse the expression and statements
                self._typing_pass.parse_expression(else_if_expression)
                for else_if_statement in else_if_statements:
                    self._typing_pass.parse_statement(else_if_statement)
        # if there is an else block, loop through its statements
        if else_statements := statement.else_statements:
            with self._typing_pass.new_scope():
                for else_statement in else_statements:
                    self._typing_pass.parse_statement(else_statement)

    def visit_import_statement(self, statement: ImportStatement) -> None:
        pass  # nothing to check in an ImportStatement

    def visit_lifecycle_statement(self, statement: LifecycleStatement) -> None:
        # create a new scope for the lifecycle statement arguments and body statements
        with self._typing_pass.new_scope():
            # add the return type (void) to the function return type stack
            self._typing_pass.function_stack.append(self._typing_pass.types["void"])
            try:
                # add the arguments to the newly created scope
                for type_token, identifier_token in statement.arguments:
                    self._typing_pass.add_identifier(identifier_token, type_token.type_)
                # check the statements inside the function
                for body_statement in statement.statements:
                    self._typing_pass.parse_statement(body_statement)
            finally:
                self._typing_pass.function_stack.pop()

    def visit_list_statement(self, statement: ListStatement) -> None:
        # add the variable declaration to the scope
        self._typing_pass.add_identifier(statement.name, statement.list_type)

    def visit_module_statement(self, statement: ModuleStatement) -> None:
        pass  # nothing to check in a ModuleStatement

    def visit_print_statement(self, statement: PrintStatement) -> None:
        # check the expression
        self._typing_pass.parse_expression(statement.value)

    def visit_return_if_value_statement(self, statement: ReturnIfValueStatement) -> None:
        # we need to type check the return_if_value statement and its expressions
        function_return_type: Type = self._typing_pass.function_stack[-1]
        non_void: bool = function_return_type.non_void()

        # if the function is a void, we can't use a return_if_value statement
        if not non_void:
            message: str = f"return_if_value statement cannot be used in a void function!"
            self._typing_pass.ast_error(message, statement.source_location)

        # check the type of the value and all expressions inside
        if statement.value:
            self._typing_pass.check_return_type(statement.value, function_return_type)
        for expression in statement.expressions:
            self._typing_pass.check_return_type(expression, function_return_type)

    def visit_return_statement(self, statement: ReturnStatement) -> None:
        # we only need to type check the return statement, the rest is already done at this point
        function_return_type: Type = self._typing_pass.function_stack[-1]
        non_void: bool = function_return_type.non_void()

        # if non_void, we need a return value
        if non_void and not statement.value:
            self._typing_pass.ast_error(f"non-void function expects a return value!", statement.source_location)

        # if void, we don't want a return value
        if not non_void and statement.value:
            message: str = f"void function expects no return value, found '{statement.value}'!"
            source_location: SourceLocation = statement.value.source_location
            self._typing_pass.ast_error(message, source_location)

        if statement.value:
            self._typing_pass.check_return_type(statement.value, function_return_type)

    def visit_var_decl_statement(self, statement: VarDeclStatement) -> None:
        # add the variable declaration to the scope (we may need it already when testing the initial value)
        self._typing_pass.add_identifier(statement.name, statement.type_token.type_)
        # get the type of the initial value
        if initial_value := statement.initial_value:
            # get the identifier token type
            requested_type: Type = self._typing_pass.get_identifier_type(statement.name)
            # check that the expression is of this type
            self._typing_pass.parse_expression(initial_value)
            # check that returned type and requested are valid
            self._typing_pass.check_types(requested_type, initial_value.type_, initial_value.source_location)
