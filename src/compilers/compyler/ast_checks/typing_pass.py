#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from ..errors.tapl_error import TaplError
from ..expressions.call_expression import CallExpression
from ..expressions.expression import Expression
from ..expressions.token_expression import TokenExpression
from .pass_base import PassBase
from ..statements.function_statement import FunctionStatement
from ..tokens.identifier_token import IdentifierToken
from ..tokens.number_token import NumberToken
from ..tokens.type_token import TypeToken
from ..types.numeric_type import NumericType
from ..types.numeric_type_type import NumericTypeType
from ..types.type import Type
from ..types.types import Types
from ..utils.ast import AST
from ..utils.source_location import SourceLocation
from ..utils.utils import Utils
from .scope_wrapper import ScopeWrapper
from ..visitors.base_expression_visitor import BaseExpressionVisitor
from ..visitors.base_statement_visitor import BaseStatementVisitor
from ..visitors.typing_pass_expression_visitor import TypingPassExpressionVisitor
from ..visitors.typing_pass_statement_visitor import TypingPassStatementVisitor
from ..visitors.verify_types_expression_visitor import VerifyTypesExpressionVisitor
from ..visitors.verify_types_statement_visitor import VerifyTypesStatementVisitor


class TypingPass(PassBase[None]):
    def __init__(self, ast: AST):
        # create the visitors of the TypingPass and pass them to the PassBase
        expression_visitor = TypingPassExpressionVisitor(ast, self)
        statement_visitor = TypingPassStatementVisitor(ast, self)
        super().__init__(ast, expression_visitor, statement_visitor)

        # extract the types as determined during the type resolving pass
        self._types: Types = ast.types

        # TODO: functions should be callable from everywhere
        # TODO: classes should be usable from everywhere

        # store a scope per class
        self.class_scopes: dict[str, ScopeWrapper] = {}
        # store a stack of function return types
        self.function_stack: list[Type] = []
        # store a stack of identifier types when they have inner identifiers
        self.identifier_stack: list[Type] = []
        # add the stdlib functions to the global scope
        self.add_stdlib_functions()

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
        self.scope_wrapper.scope.add_function(read_file_function.name.value, read_file_function)

        # add the write_file function from the standard library
        write_file_identifier: IdentifierToken = IdentifierToken(dummy_location, "write_file")
        write_file_function: FunctionStatement = FunctionStatement(bool_type_token, write_file_identifier)
        write_file_function.add_argument(string_type_token, filename_identifier)
        write_file_function.add_argument(list_char_type_token, list_identifier)
        # add the function name to the surrounding scope
        self.add_identifier(write_file_function.name, write_file_function.return_type.type_)
        # add the function to the function list
        self.scope_wrapper.scope.add_function(write_file_function.name.value, write_file_function)

    def check_function(self, function: FunctionStatement, expression: CallExpression) -> None:
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
                self.check_types(required_argument_type, passed_argument_type, source_location)
            except TaplError:
                # the type check failed, formulate a nice error for the user
                message: str = f"expected 'argument {arg_index+1}' of type "
                message += f"'{required_argument_type.keyword}', "
                message += f"but found '{passed_argument.type_.keyword}'!"
                self.ast_error(message, source_location)

    def check_types(self, left: Type, right: Type, source_location: SourceLocation) -> Type:
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

    def check_expression_types(self, left: Expression, right: Expression, source_location: SourceLocation) -> Type:
        left_type = Utils.get_expression_type(left)
        right_type = Utils.get_expression_type(right)
        return self.check_types(left_type, right_type, source_location)

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
        # create the visitors of the VerifyTypes pass
        expression_visitor: BaseExpressionVisitor[None] = VerifyTypesExpressionVisitor()
        statement_visitor: BaseStatementVisitor[None] = VerifyTypesStatementVisitor(expression_visitor)

        # loop through all statements (and expressions) and verify that they have a type
        for statement in self._ast.statements.iter():
            statement.accept(statement_visitor)
