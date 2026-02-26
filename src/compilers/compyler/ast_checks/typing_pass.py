#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from contextlib import contextmanager
from typing import Generator
from typing import NoReturn

from ..errors.ast_error import AstError
from ..errors.tapl_error import TaplError
from ..expressions.binary_expression import BinaryExpression
from ..expressions.call_expression import CallExpression
from ..expressions.expression import Expression
from ..expressions.expression_type import ExpressionType
from ..expressions.identifier_expression import IdentifierExpression
from ..expressions.string_equal_expression import StringEqualExpression
from ..expressions.string_expression import StringExpression
from ..expressions.this_expression import ThisExpression
from ..expressions.token_expression import TokenExpression
from ..expressions.type_cast_expression import TypeCastExpression
from ..expressions.unary_expression import UnaryExpression
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
from ..statements.statement import Statement
from ..statements.var_decl_statement import VarDeclStatement
from ..tokens.character_token import CharacterToken
from ..tokens.identifier_token import IdentifierToken
from ..tokens.number_token import NumberToken
from ..tokens.string_chars_token import StringCharsToken
from ..tokens.type_token import TypeToken
from ..tokens.token_type import TokenType
from ..types.character_type import CharacterType
from ..types.class_type import ClassType
from ..types.list_type import ListType
from ..types.numeric_type import NumericType
from ..types.numeric_type_type import NumericTypeType
from ..types.type import Type
from ..types.types import Types
from ..utils.ast import AST
from ..utils.source_location import SourceLocation
from ..utils.utils import Utils
from .scope_wrapper import ScopeWrapper


class TypingPass:
    # TODO: also refactor to the visitor pattern
    def __init__(self, ast: AST):
        # TODO: remove below when refactoring completed
        self._ast: AST = ast
        # store a linked list of scopes inside a wrapper that stores the functions and variables
        self._scope_wrapper: ScopeWrapper = ScopeWrapper()
        # also create a scope stash to move the scope aside for a clean one
        self._scope_wrapper_stash: ScopeWrapper = ScopeWrapper()
        # store a list of errors during this pass, if they occur
        self._errors: list[TaplError] = []

        # extract the types as determined during the type resolving pass
        self._types: Types = ast.types

        # TODO: functions should be callable from everywhere
        # TODO: classes should be usable from everywhere

        # store a scope per class
        self._class_scopes: dict[str, ScopeWrapper] = {}
        # store a stack of function return types
        self._function_stack: list[Type] = []
        # store a stack of identifier types when they have inner identifiers
        self._identifier_stack: list[Type] = []
        # add the stdlib functions to the global scope
        self.add_stdlib_functions()

    # TODO: start of base class to be removed
    def run(self) -> None:
        for statement in self._ast.statements.iter():
            self.parse_statement(statement)

        # ensure that we have the global scope and only the global scope left
        error: str = f"internal compiler error"
        assert self._scope_wrapper.scope.parent is None, f"{error}, more scopes than the global scope left!"
        # ensure that we have no scope stash left
        assert self._scope_wrapper_stash.empty, f"{error}, scope stash is not empty!"

        # if we found errors, print them and exit with exit code 1
        if self._errors:
            [print(e) for e in self._errors]
            exit(1)

    def parse_statement(self, statement: Statement | None) -> None:
        """wrapper around the statement parsing to catch and handle exceptions"""
        try:
            if statement:
                self._parse_statement(statement)
        except TaplError as e:
            self._errors.append(e)

    def add_identifier(self, identifier_token: IdentifierToken, type_: Type):
        """first checks if the identifier already exists in innermost scope, otherwise adds identifier"""
        identifier: str = identifier_token.value
        # check in the innermost scope if the identifier already exists
        if identifier in self._scope_wrapper.scope.identifiers:
            self.ast_error(f"identifier '{identifier}' already exists!", identifier_token.source_location)

        # otherwise add the identifier in the innermost scope
        self._scope_wrapper.scope.add_identifier(identifier, type_)

    def _add_function(self, name: str, function_statement: FunctionStatement):
        """first checks if the function already exists in innermost scope, otherwise adds function"""
        # check in the innermost scope if the function already exists
        if name in self._scope_wrapper.scope.functions:
            self.ast_error(f"function '{name}' already exists!", function_statement.source_location)

        # otherwise add the identifier in the innermost scope
        self._scope_wrapper.scope.add_function(name, function_statement)

    def get_identifier_type(self, identifier_token: IdentifierToken) -> Type:
        """checks that the identifier exists in current or inner scopes, and return its type"""
        identifier: str = identifier_token.value
        if type_ := self._scope_wrapper.scope.get_identifier(identifier):
            return type_

        # the identifier doesn't exist, raise an error
        self.ast_error(f"unknown identifier '{identifier}'!", identifier_token.source_location)

    @contextmanager
    def new_scope(self) -> Generator[None]:
        """enter a new outer scope for the content in the 'with' statement"""
        try:
            # first enter the scope by adding a new outer scope
            self._scope_wrapper.add_scope()
            # then give control to the caller
            yield
        finally:
            # no matter if there is an exception, leave the outer scope
            print(f"leaving scope with identifiers: {{{', '.join(self._scope_wrapper.scope.identifiers.keys())}}}")
            self._scope_wrapper.remove_scope()

    @contextmanager
    def _clean_scope(self) -> Generator[ScopeWrapper]:
        """create a new clean scope for the content in the 'with' statement"""
        try:
            # make sure the scope stash is currently empty
            assert self._scope_wrapper_stash.empty, "internal compiler error, clean scope already active!"
            # move the scope to the stash and create an empty scope list
            self._scope_wrapper_stash: ScopeWrapper = self._scope_wrapper
            self._scope_wrapper: ScopeWrapper = ScopeWrapper()
            # then give control to the caller
            yield self._scope_wrapper
        finally:
            # no matter if there is an exception, restore the scope from the stash
            # create a reference to the clean scope to return
            clean_scope: ScopeWrapper = self._scope_wrapper
            # restore the scope from the stash
            assert not self._scope_wrapper_stash.empty, "internal compiler error, no scope stash found!"
            self._scope_wrapper: ScopeWrapper = self._scope_wrapper_stash
            # create a new empty scope stash
            self._scope_wrapper_stash = ScopeWrapper()
            print(f"returning scope with identifiers: {{{', '.join(clean_scope.scope.all_identifiers)}}}")

    def ast_error(self, message: str, source_location: SourceLocation) -> NoReturn:
        """constructs and raises an AStError"""
        raise AstError(message, self._ast.filename, source_location)

    # TODO: end of base class to be removed

    def add_stdlib_functions(self) -> None:
        # TODO: do this only once, not for every class scope
        # add the functions from the standard library to the functions list
        dummy_location: SourceLocation = SourceLocation(0, 0)
        # add a bool type token
        bool_type: Type | None = self._types.get("bool")
        assert bool_type
        bool_type_token: TypeToken = TypeToken(dummy_location, bool_type)
        # add a string type token and filename identifier
        string_type: Type | None = self._types.get("string")
        assert string_type
        string_type_token: TypeToken = TypeToken(dummy_location, string_type)
        filename_identifier: IdentifierToken = IdentifierToken(dummy_location, "filename")
        # add a list[char] type token and list identifier
        list_char_type: Type | None = self._types.get("list[char]")
        assert list_char_type
        list_char_type_token: TypeToken = TypeToken(dummy_location, list_char_type)
        list_identifier: IdentifierToken = IdentifierToken(dummy_location, "list")

        # add the read_file function from the standard library
        read_file_identifier: IdentifierToken = IdentifierToken(dummy_location, "read_file")
        read_file_function: FunctionStatement = FunctionStatement(bool_type_token, read_file_identifier)
        read_file_function.add_argument(string_type_token, filename_identifier)
        read_file_function.add_argument(list_char_type_token, list_identifier)
        # add the function name to the surrounding scope
        self.add_identifier(read_file_function.name, read_file_function.return_type.type_)
        # add the function to the function list
        self._scope_wrapper.scope.add_function(read_file_function.name.value, read_file_function)

        # add the write_file function from the standard library
        write_file_identifier: IdentifierToken = IdentifierToken(dummy_location, "write_file")
        write_file_function: FunctionStatement = FunctionStatement(bool_type_token, write_file_identifier)
        write_file_function.add_argument(string_type_token, filename_identifier)
        write_file_function.add_argument(list_char_type_token, list_identifier)
        # add the function name to the surrounding scope
        self.add_identifier(write_file_function.name, write_file_function.return_type.type_)
        # add the function to the function list
        self._scope_wrapper.scope.add_function(write_file_function.name.value, write_file_function)

    def _parse_statement(self, statement: Statement) -> None:
        # TODO: refactor this and _parse_expression to a visitor pattern?
        match statement:
            case AssignmentStatement():
                # get the identifier token type
                self.parse_expression(statement.expression)
                # check that the expression is of this type
                self.parse_expression(statement.value)
                # check that returned type and requested are valid
                self._check_expression_types(statement.expression, statement.value, statement.value.source_location)
            case BreakStatement():
                pass  # nothing to check in a BreakStatement
            case BreakallStatement():
                pass  # nothing to check in a BreakallStatement
            case ClassStatement():
                with self._clean_scope() as class_scope:
                    self._class_scopes[statement.class_type.keyword] = class_scope
                    # add the stdlib functions to the class scope
                    self.add_stdlib_functions()
                    # parse the variables in the class
                    for variable in statement.variables:
                        self.parse_statement(variable)
                    # parse the statements in the lifecycle functions
                    if statement.constructor:
                        self.parse_statement(statement.constructor)
                    if statement.destructor:
                        self.parse_statement(statement.destructor)
                    for function in statement.functions:
                        # TODO: fix assert that happens when using undeclared variables in functions
                        self.parse_statement(function)
            case ContinueStatement():
                pass  # nothing to check in a ContinueStatement
            case ExpressionStatement():
                # check the expression
                self.parse_expression(statement.expression)
            case ForLoopStatement():
                # create a new scope for the for loop definition and body statements
                with self.new_scope():
                    # check the statements and expression that make up the for loop definition
                    self.parse_statement(statement.init)
                    if statement.check:
                        self.parse_expression(statement.check)
                    if statement.loop:
                        self.parse_statement(statement.loop)
                    # check all statements inside the body of the for loop
                    for body_statement in statement.statements:
                        self.parse_statement(body_statement)
            case FunctionStatement():
                # add the function name to the surrounding scope
                self.add_identifier(statement.name, statement.return_type.type_)
                # add the function statement also to the scope
                self._scope_wrapper.scope.add_function(statement.name.value, statement)
                # create a new scope for the function arguments and body statements
                with self.new_scope():
                    # add the return type to the function return type stack
                    self._function_stack.append(statement.return_type.type_)
                    try:
                        # add the arguments to the newly created scope
                        for type_token, identifier_token in statement.arguments:
                            # set the type to be a reference
                            type_token.type_.is_reference = True
                            # add the argument to the scope
                            self.add_identifier(identifier_token, type_token.type_)
                        # check the statements inside the function
                        for body_statement in statement.statements:
                            self.parse_statement(body_statement)
                    finally:
                        self._function_stack.pop()
            case IfStatement():
                # pretty nice, this parsing is the same as the scoping pass :)
                # create a new scope for the if statement expression and body
                with self.new_scope():
                    # parse the expression and statements
                    self.parse_expression(statement.expression)
                    for body_statement in statement.statements:
                        self.parse_statement(body_statement)
                # loop through all else-if blocks
                for else_if_expression, else_if_statements in statement.else_if_statement_blocks:
                    # create a new scope for the else-if block expression and body
                    with self.new_scope():
                        # parse the expression and statements
                        self.parse_expression(else_if_expression)
                        for else_if_statement in else_if_statements:
                            self.parse_statement(else_if_statement)
                # if there is an else block, loop through its statements
                if else_statements := statement.else_statements:
                    with self.new_scope():
                        for else_statement in else_statements:
                            self.parse_statement(else_statement)
            case LifecycleStatement():
                # create a new scope for the lifecycle statement arguments and body statements
                with self.new_scope():
                    # add the return type (void) to the function return type stack
                    self._function_stack.append(self._types["void"])
                    try:
                        # add the arguments to the newly created scope
                        for type_token, identifier_token in statement.arguments:
                            self.add_identifier(identifier_token, type_token.type_)
                        # check the statements inside the function
                        for body_statement in statement.statements:
                            self.parse_statement(body_statement)
                    finally:
                        self._function_stack.pop()
            case ListStatement():
                # add the variable declaration to the scope
                self.add_identifier(statement.name, statement.list_type)
            case PrintStatement():
                # check the expression
                self.parse_expression(statement.value)
            case ReturnStatement():
                # we only need to type check the return statement, the rest is already done at this point
                function_return_type: Type = self._function_stack[-1]
                non_void: bool = function_return_type.non_void()
                if non_void and not statement.value:
                    # if non_void, we need a return value
                    self.ast_error(f"non-void function expects a return value!", statement.source_location)
                if not non_void and statement.value:
                    # if void, we don't want a return value
                    message: str = f"void function expects no return value, found '{statement.value}'!"
                    source_location: SourceLocation = statement.value.source_location
                    self.ast_error(message, source_location)
                if statement.value:
                    self.parse_expression(statement.value)
                    return_value_type: Type = Utils.get_expression_type(statement.value)
                    source_location: SourceLocation = statement.value.source_location
                    try:
                        # perform type checking on the requested return type and provided return value,
                        # and catch an exception if it occurs
                        self._check_types(function_return_type, return_value_type, source_location)
                    except TaplError:
                        # the type check failed, formulate a nice error for the user
                        message: str = f"expected return value of type '{function_return_type.keyword}', "
                        message += f"but found '{return_value_type.keyword}'!"
                        self.ast_error(message, source_location)
            case VarDeclStatement():
                # add the variable declaration to the scope (we may need it already when testing the initial value)
                self.add_identifier(statement.name, statement.type_token.type_)
                # get the type of the initial value
                if initial_value := statement.initial_value:
                    # get the identifier token type
                    requested_type: Type = self.get_identifier_type(statement.name)
                    # check that the expression is of this type
                    self.parse_expression(initial_value)
                    # check that returned type and requested are valid
                    initial_value_type: Type = Utils.get_expression_type(initial_value)
                    self._check_types(requested_type, initial_value_type, initial_value.source_location)
            case _:
                assert False, f"internal compiler error, {type(statement)} not handled!"

    def parse_expression(self, expression: Expression) -> None:
        """parse an expression, where exceptions are thrown toward the surrounding statement"""
        # parse all types of expressions
        match expression:
            case BinaryExpression():
                left: Expression = expression.left
                right: Expression = expression.right
                # check the left and right expression of the binary expression
                self.parse_expression(left)
                self.parse_expression(right)
                # TODO: when binary expression results in a bool, return bool type
                expression.type_ = self._check_expression_types(left, right, expression.source_location)
            case CallExpression():
                # assert that we don't have an inner expression in the identifier expression
                assert expression.expression.inner_expression is None
                identifier_token: IdentifierToken = expression.expression.identifier_token
                if self._identifier_stack:
                    # if there is a list on the identifier stack, we can call certain functions
                    type_: Type = self._identifier_stack[-1]
                    if isinstance(type_, ListType):
                        # check the arguments
                        # TODO: add type and number of arguments checking to arguments of list functions
                        for argument in expression.arguments:
                            self.parse_expression(argument)
                        if identifier_token.value in type_.callable_functions():
                            return_value_type: Type = self._types[type_.callable_functions()[identifier_token.value]]
                            expression.type_ = return_value_type
                            expression.expression.type_ = return_value_type
                            return
                    if isinstance(type_, ClassType):
                        class_keyword: str = type_.keyword
                        function_name: str = identifier_token.value
                        # add the identifier stack class type to the expression
                        expression.class_type = type_
                        if function := self._class_scopes[class_keyword].scope.get_function(function_name):
                            self._check_function(function, expression)
                            expression.type_ = function.return_type.type_
                            expression.expression.type_ = expression.type_
                            return
                    # otherwise it's not callable, add the error
                    source_location: SourceLocation = identifier_token.source_location
                    self.ast_error(f"identifier '{identifier_token}' of a '{type_}' is not callable!", source_location)
                elif function := self._scope_wrapper.scope.get_function(identifier_token.value):
                    self._check_function(function, expression)
                    # set the return type of the function as expression type
                    expression.type_ = self.get_identifier_type(identifier_token)
                    expression.expression.type_ = expression.type_
                    return
                source_location: SourceLocation = identifier_token.source_location
                self.ast_error(f"identifier '{identifier_token}' is not callable!", source_location)
            case IdentifierExpression():
                # TODO: implement
                with self.new_scope():
                    type_: Type = self.get_identifier_type(expression.identifier_token)
                    is_class: bool = isinstance(type_, ClassType)
                    if is_class:
                        expression.class_type = type_
                    self._identifier_stack.append(type_)
                    if isinstance(type_, ListType):
                        expression.list_type = type_
                    try:
                        if expression.inner_expression:
                            self.parse_expression(expression.inner_expression)
                            expression.type_ = type_
                            return
                    finally:
                        self._identifier_stack.pop()
                expression.type_ = self.get_identifier_type(expression.identifier_token)
            case StringEqualExpression():
                # check the inner expression of the string equal expression
                self.parse_expression(expression.inner)
                expression.type_ = expression.inner.type_
            case StringExpression():
                # parse all inner expression of the string, when they exist
                for element in expression.string_elements:
                    if isinstance(element, Expression):
                        self.parse_expression(element)
                expression.type_ = self._types["string"]
            case ThisExpression():
                self.parse_expression(expression.inner_expression)
                # TODO: should be class type, as it is an instance?
                expression.type_ = expression.inner_expression.type_
            case TokenExpression():
                match expression.token:
                    case CharacterToken():
                        expression.type_ = self._types["char"]
                    case NumberToken():
                        # no checking happens here so we're going to return a base type
                        expression.type_ = self._types["base"]
                    case StringCharsToken():
                        expression.type_ = self._types["string"]
                    case IdentifierToken():
                        # TODO: handle callables differently, this now results in gcc errors
                        # get the type from the identifier
                        expression.type_ = self.get_identifier_type(expression.token)
                    case _:
                        match expression.token.token_type:
                            # TODO: refactor true/false to special booleans
                            case TokenType.TRUE:
                                expression.type_ = self._types["base"]
                            case TokenType.FALSE:
                                expression.type_ = self._types["base"]
                            case TokenType.NULL:
                                # TODO: refactor when ptr implemented
                                expression.type_ = self._types["base"]
                            case _:
                                token: str = str(type(expression.token))
                                token_type: str = expression.token.token_type.value
                                message: str = f"token {token} with TokenType {token_type} not handled!"
                                assert False, f"internal compiler error, {message}"
            case TypeCastExpression():
                # get the type of the inner expression
                self.parse_expression(expression.expression)
                inner_type: Type = Utils.get_expression_type(expression.expression)
                cast_to_type: Type = expression.cast_to.type_
                # check that both are castable
                inner_type_castable: bool = isinstance(inner_type, (CharacterType, NumericType))
                cast_to_type_castable: bool = isinstance(cast_to_type, (CharacterType, NumericType))
                # we allow any NumericType and CharacterType to be type casted, otherwise we fail
                if inner_type_castable and cast_to_type_castable:
                    expression.type_ = cast_to_type
                else:
                    message: str = f"cannot type cast from '{inner_type.keyword}' to '{cast_to_type.keyword}'!"
                    self.ast_error(message, expression.source_location)
            case UnaryExpression():
                # first parse the inner expression, and get its type
                self.parse_expression(expression.expression)
                inner_type: Type = Utils.get_expression_type(expression.expression)
                if expression.expression_type == ExpressionType.GROUPING:
                    # if it's a grouping, anything goes, our type is the inner type
                    expression.type_ = inner_type
                else:
                    # otherwise it must be a numeric type
                    if not isinstance(inner_type, NumericType):
                        message: str = f"expected numeric type for unary expression '{expression.expression_type.name}'"
                        message += f", found '{inner_type.keyword}'!"
                        self.ast_error(message, expression.expression.source_location)
                    expression.type_ = inner_type
                    # TODO: NOT should end up with a bool type
            case _:
                assert False, f"internal compiler error, {type(expression)} not handled!"

    def _check_function(self, function: FunctionStatement, expression: CallExpression) -> None:
        identifier_token: IdentifierToken = expression.expression.identifier_token
        # check that the amount of arguments are correct
        required_arguments: int = len(function.arguments)
        passed_arguments: int = len(expression.arguments)
        if len(function.arguments) != len(expression.arguments):
            message: str = f"'{identifier_token}' expected {required_arguments} argument(s), "
            message += f"but {passed_arguments} were passed!"
            self.ast_error(message, expression.source_location)
        # for all arguments, check the types
        for arg_index in range(required_arguments):
            # get the type of the required argument
            required_argument_type_token: TypeToken = function.arguments[arg_index][0]
            required_argument_type: Type = required_argument_type_token.type_
            # get the type of the passed argument
            passed_argument: Expression = expression.arguments[arg_index]
            self.parse_expression(passed_argument)
            source_location: SourceLocation = passed_argument.source_location
            # check that the types are correct
            try:
                # perform the type check, and catch an exception if it occurs
                passed_argument_type: Type = Utils.get_expression_type(passed_argument)
                self._check_types(required_argument_type, passed_argument_type, source_location)
            except TaplError:
                # the type check failed, formulate a nice error for the user
                message: str = f"expected 'argument {arg_index+1}' of type "
                message += f"'{required_argument_type.keyword}', "
                message += f"but found '{passed_argument.type_.keyword}'!"
                self.ast_error(message, source_location)

    def _check_identifier(self, identifier_token: IdentifierToken, target_type: Type) -> None:
        identifier_type: Type = self.get_identifier_type(identifier_token)
        if identifier_type != target_type:
            message: str = f"identifier {identifier_token.value} is of type {identifier_type.keyword}, "
            message += f"cannot assign value of type {target_type.keyword}!"
            self.ast_error(message, identifier_token.source_location)

    def _check_types(self, left: Type, right: Type, source_location: SourceLocation) -> Type:
        # TODO: we should check the size of a base type if the other side is no base type with _check_number_token(...)
        # check if they are both number types
        if isinstance(left, NumericType) and isinstance(right, NumericType):
            # check if there are two base types
            if left.keyword == "base" and right.keyword == "base":
                # return the base type as type
                return left
            if left.keyword == "base":
                # return the right side, as left is a base type
                return right
            if right.keyword == "base":
                # return the left side, as right is a base type
                return left

        # if both sides are not NumericType, the types must match exactly
        if left.keyword == right.keyword:
            return left

        # TODO: allow for a custom error message in this function
        # otherwise we have conflicting types, generate an error
        message: str = f"invalid types provided, '{left.keyword}' and '{right.keyword}' can't be used together!"
        self.ast_error(message, source_location)

    def _check_expression_types(self, left: Expression, right: Expression, source_location: SourceLocation) -> Type:
        left_type = Utils.get_expression_type(left)
        right_type = Utils.get_expression_type(right)
        return self._check_types(left_type, right_type, source_location)

    def _check_number_token(self, requested_type: Type, expression: TokenExpression) -> Type:
        # TODO: add num bits to the token itself, instead of calculating it here

        # type sanity checks
        assert type(requested_type) == NumericType
        assert type(expression.token) == NumberToken

        # check the value of the provided NumberToken and the requested type
        match requested_type.numeric_type_type:
            case NumericTypeType.SIGNED:
                # TODO: this will overflow in the non-python compiler
                max_value: int = 2 ** (requested_type.num_bits - 1) - 1  # 0x7F~ -> 127~
                min_value: int = -max_value - 1  # 0x80~ -> -128~
            case NumericTypeType.UNSIGNED:
                # TODO: this will overflow in the non-python compiler
                max_value: int = 2 ** (requested_type.num_bits) - 1  # 0xFF~ -> 255~
                min_value: int = 0  # 0x00~ -> 0
            case NumericTypeType.FLOATING_POINT:
                # nothing to check here
                return requested_type

        # signed/unsigned numbers must fit the num_bits
        value: int = expression.token.value
        if value < min_value or value > max_value:
            message: str = f"can't assign '{value}' to '{requested_type.keyword}', "
            message += f"value must be between [{min_value}, {max_value}]!"
            self.ast_error(message, expression.source_location)

        # all checks passed, return the requested type
        return requested_type

    def verify_types(self) -> None:
        # TODO: refactor this to a list in a statement/expression,
        # that contains all child statements/expressions, to easily recurse everything
        # ensure that all expressions have a type
        for statement in self._ast.statements.iter():
            self._check_statement(statement)

    def _check_statement(self, statement: Statement) -> None:
        match statement:
            case AssignmentStatement():
                self._check_expression(statement.expression)
                self._check_expression(statement.value)
            case BreakStatement():
                pass  # nothing to check in a BreakStatement
            case BreakallStatement():
                pass  # nothing to check in a BreakallStatement
            case ClassStatement():
                if statement.constructor:
                    self._check_statement(statement.constructor)
                if statement.destructor:
                    self._check_statement(statement.destructor)
                for function in statement.functions:
                    self._check_statement(function)
                for variable in statement.variables:
                    self._check_statement(variable)
            case ContinueStatement():
                pass  # nothing to check in a ContinueStatement
            case ExpressionStatement():
                self._check_expression(statement.expression)
            case ForLoopStatement():
                if statement.check:
                    self._check_expression(statement.check)
                if statement.init:
                    self._check_statement(statement.init)
                if statement.loop:
                    self._check_statement(statement.loop)
                for stm in statement.statements:
                    self._check_statement(stm)
            case FunctionStatement():
                for stm in statement.statements:
                    self._check_statement(stm)
            case IfStatement():
                for expression, stmlist in statement.else_if_statement_blocks:
                    self._check_expression(expression)
                    for stm in stmlist:
                        self._check_statement(stm)
                if statement.else_statements:
                    for stm in statement.else_statements:
                        self._check_statement(stm)
                self._check_expression(statement.expression)
                for stm in statement.statements:
                    self._check_statement(stm)
            case LifecycleStatement():
                for stm in statement.statements:
                    self._check_statement(stm)
            case ListStatement():
                pass  # nothing to check in a ListStatement
            case PrintStatement():
                self._check_expression(statement.value)
            case ReturnStatement():
                if statement.value:
                    self._check_expression(statement.value)
            case VarDeclStatement():
                if statement.initial_value:
                    self._check_expression(statement.initial_value)

            case _:
                assert False, f"internal compiler error, {type(statement)} not handled!"

    def _check_expression(self, expression: Expression) -> None:
        if expression.type_ == Type.unknown():
            print(f"FAILURE: {expression}.type_ == Type.unknown()")
        assert expression.type_ != Type.unknown()
        match expression:
            case BinaryExpression():
                self._check_expression(expression.left)
                self._check_expression(expression.right)
            case CallExpression():
                self._check_expression(expression.expression)
                for argument in expression.arguments:
                    self._check_expression(argument)
            case IdentifierExpression():
                if expression.inner_expression:
                    self._check_expression(expression.inner_expression)
            case StringEqualExpression():
                self._check_expression(expression.inner)
            case StringExpression():
                for element in expression.string_elements:
                    if isinstance(element, Expression):
                        self._check_expression(element)
            case ThisExpression():
                self._check_expression(expression.inner_expression)
            case TokenExpression():
                pass  # nothing to check in a TokenExpression
            case TypeCastExpression():
                self._check_expression(expression.expression)
            case UnaryExpression():
                self._check_expression(expression.expression)
            case _:
                assert False, f"internal compiler error, {type(expression)} not handled!"
