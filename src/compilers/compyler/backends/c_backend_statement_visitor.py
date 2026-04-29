#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .c_backend_state import CBackendState
from .c_backend_expression_visitor import CBackendExpressionVisitor
from ..expressions.expression import Expression
from ..expressions.string_expression import StringExpression
from ..statements.assignment_statement import AssignmentStatement
from ..statements.break_statement import BreakStatement
from ..statements.breakall_statement import BreakallStatement
from ..statements.class_statement import ClassStatement
from ..statements.continue_statement import ContinueStatement
from ..statements.expression_statement import ExpressionStatement
from ..statements.for_loop_statement import ForLoopStatement
from ..statements.function_statement import FunctionStatement
from ..statements.if_statement import IfStatement
from ..statements.import_statement import ImportStatement
from ..statements.lifecycle_statement import LifecycleStatement
from ..statements.lifecycle_statement_type import LifecycleStatementType
from ..statements.list_statement import ListStatement
from ..statements.module_statement import ModuleStatement
from ..statements.print_statement import PrintStatement
from ..statements.return_statement import ReturnStatement
from ..statements.statement import Statement
from ..statements.var_decl_statement import VarDeclStatement
from ..utils.utils import Utils
from ..visitors.base_statement_visitor import BaseStatementVisitor


class CBackendStatementVisitor(BaseStatementVisitor[str]):
    def __init__(self, state: CBackendState, expression_visitor: CBackendExpressionVisitor):
        self._state: CBackendState = state
        self._expression_visitor: CBackendExpressionVisitor = expression_visitor

    def visit_assignment_statement(self, statement: AssignmentStatement) -> str:
        identifier: str = statement.expression.accept(self._expression_visitor)
        assignment_form: str = statement.assignment_token.token_type.value
        value: str = statement.value.accept(self._expression_visitor)

        return f"{identifier} {assignment_form} {value};"

    def visit_break_statement(self, statement: BreakStatement) -> str:
        return "break;"

    def visit_breakall_statement(self, statement: BreakallStatement) -> str:
        return f"goto {statement.breakall_label};"

    def visit_class_statement(self, statement: ClassStatement) -> str:
        """returns the full class as a struct"""
        # start with the typedef
        code: str = f"typedef struct {statement.class_type}_struct {statement.class_type};\n"

        # add the class name
        code += f"struct {statement.class_type}_struct {{\n"

        # add all variables
        for variable in statement.variables:
            code += f"{variable.accept(self)}"

        # end with the closing bracket
        code += f"}};\n"

        # add the constructor, or an empty constructor if there isn't any
        constructor: LifecycleStatement = statement.constructor or LifecycleStatement(
            LifecycleStatementType.CONSTRUCTOR, statement.class_type, statement.source_location
        )
        code += f"{constructor.accept(self)}\n"

        # add the destructor or an empty destructor if there isn't any
        destructor: LifecycleStatement = statement.destructor or LifecycleStatement(
            LifecycleStatementType.DESTRUCTOR, statement.class_type, statement.source_location
        )
        code += f"{destructor.accept(self)}\n"

        # add the methods to the class
        try:
            # set the in_class flag to True so that the methods are added to the class, and not the functions header
            self._state.in_class = True
            for method in statement.functions:
                code += f"{method.accept(self)}"
        finally:
            self._state.in_class = False
        # add the class object to the state to be written to the classes header file later
        self._state.class_objects.append(code)

        # nothing to add to the main c file for the class definition
        return ""

    def visit_continue_statement(self, statement: ContinueStatement) -> str:
        return "continue;"

    def visit_expression_statement(self, statement: ExpressionStatement) -> str:
        expression_code: str = statement.expression.accept(self._expression_visitor)

        return f"{expression_code};"

    def visit_for_loop_statement(self, statement: ForLoopStatement) -> str:
        # construct the for-loop statement
        init_code: str = statement.init.accept(self) if statement.init else ""
        check_code: str = statement.check.accept(self._expression_visitor) if statement.check else ""
        loop_code: str = statement.loop.accept(self) if statement.loop else ""

        # strip the ';' if it is already in the init_code and loop_code
        init_code = init_code.removesuffix(";")
        loop_code = loop_code.removesuffix(";")

        # add the for-loop statement itself
        code: str = f"for ({init_code}; {check_code}; {loop_code}) {{\n"

        # followed by the statements in the for-loop block
        for body_statement in statement.statements:
            code += f"{body_statement.accept(self)}\n"

        # and end with the closing brace
        code += f"}}"

        # if this is the outer loop, add a breakall label here where a 'breakall' jumps to
        if statement.breakall_label:
            code += f"\n{statement.breakall_label}:;"

        return code

    def visit_function_statement(self, statement: FunctionStatement) -> str:
        """returns declaration and body of the function"""

        # utility functions used in this FunctionStatement
        def _c_declaration_base() -> str:
            """returns the function declaration line, without anything after the closing paren"""
            # start with the function return type and name
            code: str = f"{statement.return_type.name} {statement.function_name()}("

            # create a list of argument type-name pairs
            arguments: list[str] = []
            # if this is a class, also add the this pointer to the function
            if statement.class_type:
                arguments.append(f"{statement.class_type}* this")
            # construct the function declaration arguments from the list of arguments
            for argument_type, argument_name in statement.arguments:
                arguments.append(f"{argument_type.name} {argument_name}")
            # add comma separated list of the argument type-name pairs
            code += ", ".join(arguments)
            code += f")"

            return code

        code: str = f"{_c_declaration_base()} {{\n"

        # add the statements if they exist
        for inner_statement in statement.statements:
            code += f"{inner_statement.accept(self)}\n"

        # end with the closing bracket
        code += f"}}"

        # if we're generating code for a class, add the function declaration and definition to the class
        if self._state.in_class:
            self._state.class_method_declarations.append(f"{_c_declaration_base()};\n")
            self._state.class_method_definitions.append(code)
        else:
            # add the function declaration and definition to the state to be written to the functions header file later
            self._state.function_declarations.append(f"{_c_declaration_base()};\n")
            self._state.function_definitions.append(code)

        # nothing to add to the main c file for the function declaration and definition
        return ""

    def visit_if_statement(self, statement: IfStatement) -> str:
        # utility functions used in this IfStatement
        def _construct_if_statement(code: str | None, expression: Expression, statements: list[Statement]) -> str:
            # add the expression in the if statement
            new_code: str = f"if ({expression.accept(self._expression_visitor)}) {{\n"
            # add the statements of the if block
            for inner_statement in statements:
                new_code += f"{inner_statement.accept(self)}\n"
            # end with the closing brace
            new_code += f"}}"

            if code:
                # append the statement to an already existing code string
                return code + new_code
            # otherwise return the newly created code
            return new_code

        # construct the if statement
        code: str = _construct_if_statement(None, statement.expression, statement.statements)

        # add the else if blocks if they exist
        for else_expression, statements in statement.else_if_statement_blocks:
            # add the else line
            code += f" else "
            # add the else-if statement
            code: str = _construct_if_statement(code, else_expression, statements)

        # add the else block if it exists
        if statement.else_statements is not None:
            # add the else line
            code += f" else {{\n"
            for inner_statement in statement.else_statements:
                code += f"{inner_statement.accept(self)}\n"
            # end with the closing brace
            code += f"}}"

        return code

    def visit_import_statement(self, statement: ImportStatement) -> str:
        return ""  # nothing to generate for an ImportStatement

    def visit_lifecycle_statement(self, statement: LifecycleStatement) -> str:
        """returns the declaration and body of the lifecycle statement"""

        # utility functions used in this LifecycleStatement
        def _c_declaration_base() -> str:
            code: str = f""

            # add the declaration
            match statement.statement_type:
                case LifecycleStatementType.CONSTRUCTOR:
                    code += f"void {statement.type_.name}_constructor("
                case LifecycleStatementType.DESTRUCTOR:
                    code += f"void {statement.type_.name}_destructor("

            # create a list of argument type-name pairs, start with the pointer to the instance
            arguments: list[str] = [f"{statement.type_.name}* this"]
            for argument_type, argument_name in statement.arguments:
                arguments.append(f"{argument_type.type_.name} {argument_name}")
            # add the arguments
            code += ", ".join(arguments)
            code += f")"

            return code

        code: str = f"{_c_declaration_base()} {{\n"

        # add the statements in the lifecycle statement
        for inner_statement in statement.statements:
            code += f"{inner_statement.accept(self)}\n"

        # end with the closing bracket
        code += f"}}"

        # add the lifecycle statement declaration and definition to the class
        self._state.class_method_declarations.append(f"{_c_declaration_base()};\n")
        self._state.class_method_definitions.append(code)

        # nothing to add to the main c file for the lifecycle statement declaration and definition
        return ""

    def visit_list_statement(self, statement: ListStatement) -> str:
        list_base: str = statement.list_type.name
        # create the list declaration
        code: str = f"{list_base} {statement.name};"
        # call the constructor of the list
        code += f"{list_base}_constructor(&{statement.name});"
        return code

    def visit_module_statement(self, statement: ModuleStatement) -> str:
        return ""  # nothing to generate for a ModuleStatement

    def visit_print_statement(self, statement: PrintStatement) -> str:
        # handle the special case of a stringexpression
        if isinstance(statement.value, StringExpression):
            # pass the line_end on to the string expression
            statement.value.line_end = statement.line_end
            # print the string expression as string
            return f"printf({statement.value.accept(self._expression_visitor)});"

        type_format_string: str = Utils.get_type_format_string(statement.value)
        value = statement.value.accept(self._expression_visitor)
        return f'printf("{type_format_string}{statement.line_end}", {value});'

    def visit_return_statement(self, statement: ReturnStatement) -> str:
        if statement.value:
            return f"return {statement.value.accept(self._expression_visitor)};"
        else:
            return f"return;"

    def visit_var_decl_statement(self, statement: VarDeclStatement) -> str:
        # if we have an initial value, also generate code for that
        if statement.initial_value:
            initial_value: str = statement.initial_value.accept(self._expression_visitor)
            return f"{statement.type_token.name} {statement.name} = {initial_value};"

        # otherwise it's a default initialized variable
        return f"{statement.type_token} {statement.name};"
