#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .c_backend_state import CBackendState
from .c_backend_expression_visitor import CBackendExpressionVisitor
from ..expressions.call_expression import CallExpression
from ..expressions.expression import Expression
from ..expressions.string_expression import StringExpression
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
from ..statements.lifecycle_statement_type import LifecycleStatementType
from ..statements.list_statement import ListStatement
from ..statements.module_statement import ModuleStatement
from ..statements.print_statement import PrintStatement
from ..statements.return_if_value_statement import ReturnIfValueStatement
from ..statements.return_statement import ReturnStatement
from ..statements.statement import Statement
from ..statements.var_decl_statement import VarDeclStatement
from ..utils.enum_entry import EnumEntry
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

    def visit_enum_statement(self, statement: EnumStatement) -> str:
        # utility functions used in this EnumStatement
        def _value(entry: EnumEntry) -> str:
            return f"{statement.enum_type}_enum_{entry.name}"

        # start with the typedef
        code: str = f"typedef enum {statement.enum_type}_enum {statement.enum_type};\n"

        # add the enum name
        code += f"enum {statement.enum_type}_enum {{\n"

        # add all enum entries
        for entry in statement.get_entries():
            code += f"{_value(entry)} = {entry.value.accept(self._expression_visitor)},\n"

        # end with the closing bracket
        code += f"}};\n"

        # add the code to the state to be written to the enums header file
        self._state.enum_definitions.append(code)

        # start with a new code block and add the enum to string function definition
        code = f"const char* {statement.enum_type}_enum_to_string({statement.enum_type} value) {{\n"

        # add the switch statement for the enum to string function
        code += f"switch (value) {{\n"

        # add all enum entries to the switch statement
        for entry in statement.get_entries():
            code += f"case {_value(entry)}:\n"
            code += f"return {entry.string_value.accept(self._expression_visitor)};\n"

        # end the switch statement
        code += f"}}\n"

        # add the default case for the switch statement
        code += f'return "Unknown {statement.enum_type} value";\n'

        # end the enum to string function definition
        code += f"}}\n"

        # add the code to the state to be written to the enums header file
        self._state.enum_to_string_definitions.append(code)

        # nothing to add to the main c file for the enum definition
        return ""

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

        self._state.function_return_type = statement.return_type.name
        try:
            # add the statements if they exist
            for inner_statement in statement.statements:
                code += f"{inner_statement.accept(self)}\n"
        finally:
            self._state.function_return_type = ""

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
                    code += f"void {statement.type_}_constructor("
                case LifecycleStatementType.DESTRUCTOR:
                    code += f"void {statement.type_}_destructor("

            # create a list of argument type-name pairs, start with the pointer to the instance
            arguments: list[str] = [f"{statement.type_}* this"]
            for argument_type, argument_name in statement.arguments:
                arguments.append(f"{argument_type.type_} {argument_name}")
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

    def visit_return_if_value_statement(self, statement: ReturnIfValueStatement) -> str:
        # make sure we have a function return type
        return_type: str = self._state.function_return_type
        assert return_type

        # check the value in the statement, otherwise it's the null value
        if statement.value:
            # when a value is provided, check for equality with that value
            check: str = f"retval == {statement.value.accept(self._expression_visitor)}"
        else:
            # when no value is provided, check for non-null
            check: str = f"retval != {Utils.null_value()}"

        # generate the if and return statements for all expressions
        code: str = ""
        for expression in statement.expressions:
            code += f"{{\n"
            code += f"{return_type} retval = {expression.accept(self._expression_visitor)};\n"
            code += f"if ({check}) return retval;\n"
            code += f"}}\n"
        return code

    def visit_return_statement(self, statement: ReturnStatement) -> str:
        if statement.value:
            return f"return {statement.value.accept(self._expression_visitor)};"
        else:
            return f"return;"

    def visit_var_decl_statement(self, statement: VarDeclStatement) -> str:
        code: str = ""

        if statement.initial_value and not statement.class_variable:
            # if we have an initial value, that is not a constructor call, also generate code for that
            initial_value: str = statement.initial_value.accept(self._expression_visitor)
            code += f"{statement.type_token.name} {statement.name} = {initial_value};"
        else:
            # otherwise it's a default initialized variable
            code += f"{statement.type_token} {statement.name};"

        # if it is a class variable, also call the constructor for the variable
        if statement.class_variable:
            # formulate the constructor call, start with the variable name reference
            arguments: list[str] = [f"&{statement.name}"]

            # if we have an initial value, it must be a constructor call, so check this and add the arguments
            if statement.initial_value:
                assert isinstance(statement.initial_value, CallExpression)
                for argument in statement.initial_value.arguments:
                    arguments.append(argument.accept(self._expression_visitor))

            # create the comma separated list of arguments for the constructor call
            arguments_string: str = ", ".join(arguments)

            # add the full constructor statement with the arguments
            code += f"\n{statement.type_token.name}_constructor({arguments_string});"

        return code
