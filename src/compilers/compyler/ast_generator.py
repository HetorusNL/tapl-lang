#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path
from typing import NoReturn

from .errors.tapl_error import TaplError
from .errors.ast_error import AstError
from .expressions.binary_expression import BinaryExpression
from .expressions.call_expression import CallExpression
from .expressions.expression import Expression
from .expressions.identifier_expression import IdentifierExpression
from .expressions.string_equal_expression import StringEqualExpression
from .expressions.string_expression import StringExpression
from .expressions.this_expression import ThisExpression
from .expressions.token_expression import TokenExpression
from .expressions.type_cast_expression import TypeCastExpression
from .expressions.unary_expression import UnaryExpression
from .expressions.expression_type import ExpressionType
from .statements.assignment_statement import AssignmentStatement
from .statements.break_statement import BreakStatement
from .statements.breakall_statement import BreakallStatement
from .statements.class_statement import ClassStatement
from .statements.continue_statement import ContinueStatement
from .statements.expression_statement import ExpressionStatement
from .statements.for_loop_statement import ForLoopStatement
from .statements.function_statement import FunctionStatement
from .statements.if_statement import IfStatement
from .statements.lifecycle_statement import LifecycleStatement
from .statements.lifecycle_statement_type import LifecycleStatementType
from .statements.list_statement import ListStatement
from .statements.print_statement import PrintStatement
from .statements.return_statement import ReturnStatement
from .statements.statement import Statement
from .statements.var_decl_statement import VarDeclStatement
from .tokens.identifier_token import IdentifierToken
from .tokens.token import Token
from .tokens.type_token import TypeToken
from .tokens.token_type import TokenType
from .types.class_type import ClassType
from .types.list_type import ListType
from .types.type import Type
from .types.types import Types
from .utils.ast import AST
from .utils.source_location import SourceLocation
from .utils.stream import Stream


class AstGenerator:
    def __init__(self, filename: Path, token_stream: Stream[Token], types: Types):
        self._token_stream: Stream[Token] = token_stream
        self._tokens: list[Token] = token_stream.objects
        self._filename: Path = filename
        self._types: Types = types

        # some variables to store the state of the ast generator
        self._current_index: int = 0
        self._in_function: bool = False
        self._loop_count: int = 0
        self._breakall_label: str = "breakall"
        self._class_type: ClassType | None = None

    def current(self) -> Token:
        """returns the token at the current location"""
        return self._tokens[self._current_index]

    def next(self, offset: int = 1) -> Token:
        """returns the token after the current location, or at the offset, if offset is provided"""
        if self._current_index + offset > len(self._tokens):
            self.ast_error(f"unexpected end-of-file, token at offset {offset} doesn't exist!")
        return self._tokens[self._current_index + offset]

    def previous(self) -> Token:
        """returns the previous (consumed) token"""
        if self._current_index == 0:
            self.ast_error("can't call previous when no tokens have been consumed yet!")
        return self._tokens[self._current_index - 1]

    def is_at_end(self) -> bool:
        """check whether we are at the end of the token stream, or EOF token"""
        # check for end of token stream
        if self._current_index >= len(self._tokens):
            return True
        return self.current().token_type == TokenType.EOF

    def consume(self) -> Token:
        """consumes the token at the current location"""
        self._current_index += 1
        if self._current_index > len(self._tokens):
            self.ast_error("unexpected end-of-file, can't consume more tokens!")
        return self.previous()

    def match(self, *token_types: TokenType) -> Token | None:
        """returns the token if the provided token_type matches the current token"""
        if self.current().token_type in token_types:
            return self.consume()
        return None

    def expect(self, token_type: TokenType, message: str = "") -> Token:
        """expects the next token to be of token_type, return token if match, raises AstError otherwise"""
        if token := self.match(token_type):
            return token
        else:
            if not message:
                message = f"expected '{token_type}' but found '{self.current()}'!"
            self.ast_error(message)

    def expect_newline(self, type_: str = "statement", must_end_with_newline: bool = True) -> None:
        if not must_end_with_newline:
            return

        if not self.match(TokenType.NEWLINE, TokenType.EOF):
            self.ast_error(f"expected a newline or End-Of-File after {type_}, found '{self.current()}'!")

    def _has_indent(self) -> bool:
        """returns whether the next token is an indent, if so, consume it"""
        # if we're at EOF, there is no indent
        if self.is_at_end():
            return False

        # if the next token is an indent, consume it
        return self.match(TokenType.INDENT) is not None

    def _get_breakall_label(self) -> str | None:
        # if this is the outer loop, return the breakall label that's set, otherwise None
        if self._loop_count == 0:
            return self._breakall_label
        return None

    def _set_breakall_label(self, loop_token: Token) -> None:
        # if this is the outer loop, set the breakall label to the loop start location
        if self._loop_count == 0:
            self._breakall_label = f"breakall_{loop_token.source_location.start}"

    def _statement_block_in_loop(self) -> list[Statement]:
        # allow for break, breakall and continue statements inside the loop
        # increment the loop count
        self._loop_count += 1

        try:
            # get the statements in the body of the loop
            statements: list[Statement] = self._statement_block()
        finally:
            # after parsing the statements or an exception, decrement the loop count again
            self._loop_count -= 1

        return statements

    def _statement_block(self) -> list[Statement]:
        """returns a list of statements in the block, list is empty if there is no indent"""
        # we can either have an empty block or we must have an indent
        if not self._has_indent():
            return []

        # capture all statements until we get a dedent
        statements: list[Statement] = []
        while not self.match(TokenType.DEDENT):
            statement: Statement = self.statement()
            statements.append(statement)
        return statements

    def assignment_statement(self, expression: Expression, must_end_with_newline: bool) -> AssignmentStatement | None:
        # check that we have a ThisExpression or an identifier expression (return otherwise)
        if not isinstance(expression, (ThisExpression, IdentifierExpression)):
            return
        # check if there is a form of assignment, return if not
        if not AssignmentStatement.is_assignment_form_token(self.current()):
            return

        # consume the form of assignment ending in equal
        assignment_token: Token = self.expect(self.current().token_type)

        # then consume the expression
        value: Expression = self.expression()

        # statements should end with a newline
        self.expect_newline(must_end_with_newline=must_end_with_newline)

        # return the assignment statement
        return AssignmentStatement(expression, assignment_token, value)

    def for_loop_statement(self) -> ForLoopStatement | None:
        # early return if we don't have a for-loop statement
        token: Token | None = self.match(TokenType.FOR)
        if not token:
            return None

        # set the breakall label if this is the outer loop
        self._set_breakall_label(token)

        # otherwise we have an (already consumed) for-loop statement
        # start parsing the initial value statement (if it exists)
        init: Statement | None = None
        if not self.match(TokenType.SEMICOLON):
            init: Statement | None = self.statement(must_end_with_newline=False)
            self.expect(TokenType.SEMICOLON)

        # parse the check expression (if it exists)
        check: Expression | None = None
        if not self.match(TokenType.SEMICOLON):
            check: Expression | None = self.expression()
            self.expect(TokenType.SEMICOLON)

        # parse the loop statement (if it exists)
        loop: Statement | None = None
        if not self.match(TokenType.COLON):
            loop: Statement | None = self.statement(must_end_with_newline=False)
            self.expect(TokenType.COLON)

        # followed by a newline
        self.expect_newline()

        # continue with the body of the for-loop statement
        statements: list[Statement] = self._statement_block_in_loop()

        # return the finished for-loop statement
        return ForLoopStatement(token, self._get_breakall_label(), init, check, loop, statements)

    def _type_statement(
        self, must_end_with_newline: bool
    ) -> FunctionStatement | ListStatement | VarDeclStatement | None:
        """returns a statement starting with a type or list, or None otherwise"""
        # start with a type
        if self.current().token_type != TokenType.TYPE:
            return None
        # the next common token is an identifier
        if self.next(1).token_type != TokenType.IDENTIFIER:
            return None

        # check if we have a function that has an opening paren here
        # no need to handle parsing past-EOF here, as this is token exists in the stream
        if self.next(2).token_type == TokenType.PAREN_OPEN:
            return self.function_statement()

        # otherwise we have an variable declaration statement
        return self.var_decl_statement(must_end_with_newline)

    def _finish_function_statement(self, function_statement: FunctionStatement) -> FunctionStatement:
        # after the function definition itself, we expect a colon
        self.expect(TokenType.COLON)
        # followed by a newline
        self.expect_newline()

        # we're inside a function, allow return statements here
        self._in_function = True  # TODO: make exception-safe

        # continue with the body of the function
        statements: list[Statement] = self._statement_block()
        # add them to the function
        function_statement.statements = statements

        # we've finished parsing the function statements, don't allow return statements from now on
        self._in_function = False

        # return the finished function statement
        return function_statement

    def function_statement(self) -> FunctionStatement:
        # the _type_statement function already checked the tokens for us
        # so we can start consuming here
        return_type: Token = self.consume()
        assert type(return_type) == TypeToken
        name: Token = self.consume()
        assert type(name) == IdentifierToken
        function_statement: FunctionStatement = FunctionStatement(return_type, name, self._class_type)
        self.expect(TokenType.PAREN_OPEN)

        # check for a closing parenthesis, then we have a function without arguments
        if self.match(TokenType.PAREN_CLOSE):
            # finish parsing and return the function statement
            return self._finish_function_statement(function_statement)

        # consume type-name function arguments
        while True:
            argument_type: Token = self.expect(TokenType.TYPE)
            assert type(argument_type) == TypeToken
            # test that the argument type is non-void
            if not argument_type.type_.non_void():
                self.ast_error("function arguments cannot be of type void!")
            argument_name: Token = self.expect(TokenType.IDENTIFIER)
            assert type(argument_name) == IdentifierToken
            # add the argument to the function statement
            function_statement.add_argument(argument_type, argument_name)

            # if we don't have a comma, it's the end of the argument list
            if not self.match(TokenType.COMMA):
                break

        # we must end with a closing parenthesis
        self.expect(TokenType.PAREN_CLOSE)

        # finish parsing and return the function statement
        return self._finish_function_statement(function_statement)

    def _single_if_statement(self, if_statement: IfStatement | None = None) -> IfStatement | None:
        # early return if we don't have an if statement
        token: Token | None = self.match(TokenType.IF)
        if not token:
            return None

        # otherwise we have an (already consumed) if statement
        # start parsing the if statement line itself
        # first match an expression
        expression: Expression = self.expression()
        # then a colon
        self.expect(TokenType.COLON)
        # followed by a newline
        self.expect_newline()

        # continue with the body of the statement
        statements: list[Statement] = self._statement_block()

        # if we already got an if statement, add it as else-if block
        if if_statement:
            if_statement.add_else_if_statement_block(expression, statements)
            return if_statement

        # otherwise return a new if statement
        return IfStatement(token, expression, statements)

    def if_statement(self) -> IfStatement | None:
        statement: IfStatement | None = self._single_if_statement()
        # return the if statement if we found an EOF, or None if we didn't find a if statement
        if self.is_at_end() or not statement:
            return statement

        # check for else-if and else blocks
        while self.match(TokenType.ELSE):
            # check for another if, an else-if block
            if self._single_if_statement(statement):
                # found an else-if block, it has already been added, so loop back to search for more
                pass
            else:
                # found a bare else, this is the final statement block
                # first expect a colon
                self.expect(TokenType.COLON)
                # followed by a newline
                self.expect_newline()

                # now parse the statements
                statements: list[Statement] = self._statement_block()

                # add this block as the else statements to the if statement
                statement.else_statements = statements
                # nothing more in an if statement after an else, so break from the loop
                break

        # no (more) else statements, return the finished if statement
        return statement

    def print_statement(self) -> PrintStatement | None:
        # early return if we don't have a print/println statement
        token: Token | None = self.match(TokenType.PRINT, TokenType.PRINTLN)
        if not token:
            return

        # match an expression between parenthesis
        self.expect(TokenType.PAREN_OPEN)
        value = self.expression()
        self.expect(TokenType.PAREN_CLOSE)

        # statements should end with a newline
        self.expect_newline()

        return PrintStatement(token, value)

    def return_statement(self) -> ReturnStatement | None:
        # early return if we don't have a return statement
        token: Token | None = self.match(TokenType.RETURN)
        if not token:
            return

        # check if we're allowed to return, error otherwise
        if not self._in_function:
            self.ast_error(f"return statement is not allowed here!")

        # check if we have a newline
        if self.match(TokenType.NEWLINE, TokenType.EOF):
            # return the statement without value
            return ReturnStatement(token)

        # otherwise expect an expression to return
        expression: Expression = self.expression()

        # statements should end with a newline
        self.expect_newline()

        return ReturnStatement(token, expression)

    def var_decl_statement(self, must_end_with_newline: bool) -> ListStatement | VarDeclStatement:
        # the _type_statement function already checked the tokens for us
        # so we can start consuming here
        type_token: Token = self.consume()
        assert isinstance(type_token, TypeToken)
        name: Token = self.consume()
        assert isinstance(name, IdentifierToken)

        # check if there is an initial value, fall back to None
        initial_value: Expression | None = None
        if self.match(TokenType.EQUAL):
            initial_value: Expression | None = self.expression()

        # statements should end with a newline
        self.expect_newline(must_end_with_newline=must_end_with_newline)

        # check if the type is a list type or a different type
        if isinstance(type_token.type_, ListType):
            # return a list statement
            return ListStatement(type_token, name)

        return VarDeclStatement(type_token, name, initial_value)

    def while_loop_statement(self) -> ForLoopStatement | None:
        # will generate a for loop statement if a while loop is found
        # early return if we don't have a while-loop statement
        token: Token | None = self.match(TokenType.WHILE)
        if not token:
            return None

        # set the breakall label if this is the outer loop
        self._set_breakall_label(token)

        # otherwise we have an (already consumed) while-loop statement
        # parse the condition (to be placed in the check expression of the for-loop statement)
        check: Expression = self.expression()

        # followed by a colon and newline
        self.expect(TokenType.COLON)
        self.expect_newline()

        # continue with the body of the while-loop statement
        statements: list[Statement] = self._statement_block_in_loop()

        # return the finished while-loop as a for-loop statement
        return ForLoopStatement(token, self._get_breakall_label(), None, check, None, statements)

    def _finish_lifecycle_statement(self, lifecycle_statement: LifecycleStatement) -> LifecycleStatement:
        # after the lifecycle statement definition itself, we expect a colon
        self.expect(TokenType.COLON)
        # followed by a newline
        self.expect_newline()

        # we're inside a lifecycle statement, allow return statements here
        self._in_function = True  # TODO: make exception-safe

        # continue with the body of the lifecycle statement
        statements: list[Statement] = self._statement_block()
        # add them to the lifecycle statement
        lifecycle_statement.statements = statements

        # we've finished parsing the lifecycle statement statements, don't allow return statements from now on
        self._in_function = False

        # return the finished lifecycle statement
        return lifecycle_statement

    def _constructor(self, type_: Type) -> LifecycleStatement | None:
        # early return if we don't have the class type
        name: Token | None = self.match(TokenType.TYPE)
        if not name:
            return None
        assert type(name) == TypeToken
        # early return if we found a different type
        if name.type_ != type_:
            self.ast_error(f"expected {type_} in constructor, but found {name.type_}!")

        # start constructing the constructor lifecycle statement
        statement_type: LifecycleStatementType = LifecycleStatementType.CONSTRUCTOR
        constructor: LifecycleStatement = LifecycleStatement(statement_type, type_, name.source_location)

        # constructors start with an opening parenthesis
        self.expect(TokenType.PAREN_OPEN)

        # check for a closing parenthesis, then we have a constructor without arguments
        if self.match(TokenType.PAREN_CLOSE):
            # finished parsing arguments, parse the rest of the constructor
            return self._finish_lifecycle_statement(constructor)

        # consume type-name constructor arguments
        while True:
            argument_type: Token = self.expect(TokenType.TYPE)
            assert type(argument_type) == TypeToken
            # test that the argument type is non-void
            if not argument_type.type_.non_void():
                self.ast_error("function arguments cannot be of type void!")
            argument_name: Token = self.expect(TokenType.IDENTIFIER)
            assert type(argument_name) == IdentifierToken
            # add the argument to the function statement
            constructor.add_argument(argument_type, argument_name)

            # if we don't have a comma, it's the end of the argument list
            if not self.match(TokenType.COMMA):
                break

        # we must end with a closing parenthesis
        self.expect(TokenType.PAREN_CLOSE)

        # finished parsing arguments, parse the rest of the constructor
        return self._finish_lifecycle_statement(constructor)

    def _destructor(self, type_: Type) -> LifecycleStatement | None:
        # early return if we don't have a tilde
        tilde: Token | None = self.match(TokenType.TILDE)
        if not tilde:
            return None

        # check for the destructor (class) name
        name: Token | None = self.match(TokenType.TYPE)
        if not name:
            self.ast_error(f"expected {type_.keyword} in destructor!")
        assert type(name) == TypeToken
        # early return if we found a different type
        if name.type_ != type_:
            self.ast_error(f"expected {type_} in destructor, but found {name.type_}!")

        # start constructing the destructor lifecycle statement
        statement_type: LifecycleStatementType = LifecycleStatementType.DESTRUCTOR
        destructor: LifecycleStatement = LifecycleStatement(statement_type, type_, name.source_location)

        # destructor should have opening and closing parenthesis without arguments
        self.expect(TokenType.PAREN_OPEN)
        self.expect(TokenType.PAREN_CLOSE)

        # parse the rest of the destructor
        return self._finish_lifecycle_statement(destructor)

    def class_statement(self) -> ClassStatement | None:
        # will generate a class statement if a class declaration is found
        # early return if we don't have a class keyword
        token: Token | None = self.match(TokenType.CLASS)
        if not token:
            return None

        # construct the source location of the whole class
        source_location: SourceLocation = token.source_location

        # consume the class name (which is a type token)
        name: Token = self.expect(TokenType.TYPE)
        assert type(name) == TypeToken
        class_type: Type = name.type_
        assert isinstance(class_type, ClassType)
        source_location += name.source_location

        # followed by a colon and newline
        self.expect(TokenType.COLON)
        self.expect_newline()

        # check if we have an indented block
        if not self._has_indent():
            # otherwise return an empty class without any statement
            return ClassStatement(class_type, source_location)

        # we're in a class, so allow parsing class-specific syntax
        self._class_type = class_type  # TODO: make exception-safe

        # construct everything we find in the class until we get to a dedent
        class_statement: ClassStatement = ClassStatement(class_type, source_location)
        while not self.match(TokenType.DEDENT):
            # check for a var decl or function statement
            if type_statement := self._type_statement(True):
                if type(type_statement) == FunctionStatement:
                    class_statement.functions.append(type_statement)
                    continue
                elif type(type_statement) == VarDeclStatement:
                    class_statement.variables.append(type_statement)
                    continue
                elif type(type_statement) == ListStatement:
                    class_statement.variables.append(type_statement)
                    continue
                else:
                    message: str = f"expected FunctionStatement or VarDeclStatement, found '{type(type_statement)}'"
                    raise AstError(message, self._filename, type_statement.source_location)

            # check for a constructor
            if constructor := self._constructor(name.type_):
                if class_statement.constructor:
                    message = f"found a {name} constructor while another constructor was already found!"
                    raise AstError(message, self._filename, constructor.source_location)
                class_statement.constructor = constructor
                continue

            # check for a destructor
            if destructor := self._destructor(name.type_):
                if class_statement.destructor:
                    message = f"found a {name} destructor while another descructor was already found!"
                    raise AstError(message, self._filename, destructor.source_location)
                class_statement.destructor = destructor
                continue

            message: str = f"expected FunctionStatement, VarDeclStatement, Constructor or Destructor,"
            message += f" found '{self.current()}'"
            self.ast_error(message)

        # finished processing the class, we no longer allow parsing class-specific syntax
        self._class_type = None

        # return the finished class statement
        return class_statement

    def loop_control_statement(self) -> Statement | None:
        # early return if we're not inside a loop
        if self._loop_count == 0:
            return None

        # check for a break statement
        if token := self.match(TokenType.BREAK):
            self.expect_newline("break")
            return BreakStatement(token.source_location)

        # check for a breakall statement
        if token := self.match(TokenType.BREAKALL):
            self.expect_newline("breakall")
            return BreakallStatement(token.source_location, self._breakall_label)

        # check for a continue statement
        if token := self.match(TokenType.CONTINUE):
            self.expect_newline("continue")
            return ContinueStatement(token.source_location)

        return None

    def statement(self, must_end_with_newline: bool = True) -> Statement:
        """returns a statement of some kind"""
        # check for a statement starting with a type
        if statement := self._type_statement(must_end_with_newline):
            return statement

        # check for a return statement
        if statement := self.return_statement():
            return statement

        # temporary(!) print statement, printing an expression
        # TODO: replace this temporary statement with a builtin function :)
        if statement := self.print_statement():
            return statement

        # check for an if statement
        if statement := self.if_statement():
            return statement

        # check for a for-loop statement
        if statement := self.for_loop_statement():
            return statement

        # check for a while-loop statement
        if statement := self.while_loop_statement():
            return statement

        # check for a class 'statement'
        if statement := self.class_statement():
            return statement

        # if we're inside a loop, check for break, breakall, continue statements
        if statement := self.loop_control_statement():
            return statement

        # fall back to a bare expression statement
        expression: Expression = self.expression()

        # check if the expression is used in an assignment statement
        if statement := self.assignment_statement(expression, must_end_with_newline):
            return statement

        self.expect_newline("expression", must_end_with_newline)

        return ExpressionStatement(expression)

    def expression(self) -> Expression:
        """returns an expression, starts parsing at the lowest precedence level"""
        expression: Expression = self.boolean()
        return expression

    def boolean(self) -> Expression:
        """returns a boolean expression, or a higher precedence level expression"""
        expression: Expression = self.comparison()

        and_or_tokens: tuple[TokenType, ...] = (TokenType.AND_AND, TokenType.OR_OR)
        while token := self.match(*and_or_tokens):
            # we found a boolean expression token, go up the precedence list to get another expression
            right: Expression = self.comparison()
            expression = BinaryExpression(expression, token, right)

        # otherwise return the expression found at the beginning
        return expression

    def comparison(self) -> Expression:
        """returns a comparison expression, or a higher precedence level expression"""
        # go up the precedence list to get the left hand side expression
        expression: Expression = self.additive()

        boolean_expression_tokens: tuple[TokenType, ...] = (
            TokenType.EQUAL_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.NOT_EQUAL,
        )
        while token := self.match(*boolean_expression_tokens):
            # we found a comparison expression token, go up the precedence list to get another expression
            right: Expression = self.additive()
            expression = BinaryExpression(expression, token, right)

        # otherwise return the expression found at the beginning
        return expression

    def additive(self) -> Expression:
        """returns a PLUS/MINUS, or a higher precedence level expression"""
        # go up the precedence list to get the left hand side expression
        expression: Expression = self.multiplicative()

        while token := self.match(TokenType.PLUS, TokenType.MINUS):
            # we found a plus/minus token, go up the precedence list to get another expression
            right: Expression = self.multiplicative()
            expression = BinaryExpression(expression, token, right)

        # otherwise return the expression found in the beginning
        return expression

    def multiplicative(self) -> Expression:
        """returns a STAR/SLASH, or a higher precedence level expression"""
        # go up the precedence list to get the left hand side expression
        expression: Expression = self.primary()

        while token := self.match(TokenType.STAR, TokenType.SLASH):
            # we found a star/slash token, go up the precedence list to get another expression
            right: Expression = self.primary()
            expression = BinaryExpression(expression, token, right)

        # otherwise return the expression found in the beginning
        return expression

    def primary(self) -> Expression:
        """returns a primary expression: primary keywords or character/number/string"""
        # match the primary keywords
        if token := self.match(TokenType.FALSE):
            return TokenExpression(token.source_location, token)
        if token := self.match(TokenType.NULL):
            return TokenExpression(token.source_location, token)
        if token := self.match(TokenType.TRUE):
            return TokenExpression(token.source_location, token)

        # match literal characters, numbers and strings
        if token := self.match(TokenType.CHARACTER):
            return TokenExpression(token.source_location, token)
        if token := self.match(TokenType.NUMBER):
            return TokenExpression(token.source_location, token)
        if token := self.match(TokenType.STRING_START):
            # start constructing a string expression
            string_expression: StringExpression = StringExpression(token)
            while token := self.consume():
                # add the token to the string expression
                string_expression.add_token(token)
                # check for the end of the string, then we return
                if token.token_type == TokenType.STRING_END:
                    break
                # check for a start of an expression
                if token.token_type == TokenType.STRING_EXPR_START:
                    expression: Expression = self.expression()
                    # check for the end of the expression and expression modifiers
                    if self.match(TokenType.STRING_EXPR_END):
                        # found an expression end, add it to the string expression and continue
                        string_expression.add_token(expression)
                    elif equal_token := self.match(TokenType.EQUAL):
                        # found a string equal expression, add it to the string expression and continue
                        string_expression.add_token(StringEqualExpression(expression, equal_token, self._filename))
                    # later expression format modifiers can be added here as well

            return string_expression

        # match expressions between parenthesis
        if paren_open := self.match(TokenType.PAREN_OPEN):
            # check if this is a type casting
            if type_ := self.match(TokenType.TYPE):
                assert isinstance(type_, TypeToken)
                # expect a closing parenthesis
                self.expect(TokenType.PAREN_CLOSE)
                # followed by a primary expression that is type casted
                primary: Expression = self.primary()
                # the SourceLocation is from paren_open till the primary expression
                source_location: SourceLocation = paren_open.source_location + primary.source_location
                return TypeCastExpression(source_location, type_, primary)

            # otherwise it's a grouping expression
            expression: Expression = self.expression()
            message = f"expected closing parenthesis, but found '{self.current()}'!"
            paren_close: Token = self.expect(TokenType.PAREN_CLOSE, message)
            # the SourceLocation is from paren_open till paren_close and everything in between
            source_location: SourceLocation = paren_open.source_location + paren_close.source_location
            return UnaryExpression(source_location, ExpressionType.GROUPING, expression)

        # match comparison not expression
        if not_token := self.match(TokenType.NOT):
            expression: Expression = self.primary()
            source_location: SourceLocation = not_token.source_location + expression.source_location
            return UnaryExpression(source_location, ExpressionType.NOT, expression)

        # match unary minus expression
        if minus_token := self.match(TokenType.MINUS):
            expression: Expression = self.primary()
            source_location: SourceLocation = minus_token.source_location + expression.source_location
            return UnaryExpression(source_location, ExpressionType.MINUS, expression)

        # match pre increment or decrement expression
        if increment_token := self.match(TokenType.INCREMENT):
            identifier: Token = self.expect(TokenType.IDENTIFIER)
            expression: Expression = TokenExpression(identifier.source_location, identifier)
            source_location: SourceLocation = increment_token.source_location + expression.source_location
            return UnaryExpression(source_location, ExpressionType.PRE_INCREMENT, expression)
        if decrement_token := self.match(TokenType.DECREMENT):
            identifier: Token = self.expect(TokenType.IDENTIFIER)
            expression: Expression = TokenExpression(identifier.source_location, identifier)
            source_location: SourceLocation = decrement_token.source_location + expression.source_location
            return UnaryExpression(source_location, ExpressionType.PRE_DECREMENT, expression)

        # match an identifier
        if token := self.match(TokenType.IDENTIFIER):
            assert isinstance(token, IdentifierToken)
            return self.identifier_expression(token)

        # match a this-expression
        if this := self.match(TokenType.THIS):
            source_location: SourceLocation = this.source_location
            # check that we're allowed to use this here
            if self._class_type is None:
                self.ast_error(f"found 'this' while not in a class!")
            # we expect a dot after this
            self.expect(TokenType.DOT)
            # expect a nested identifier
            identifier: Token = self.expect(TokenType.IDENTIFIER)
            assert isinstance(identifier, IdentifierToken)
            expression: Expression = self.identifier_expression(identifier)
            source_location += expression.source_location
            # construct and return the this-expression
            return ThisExpression(source_location, expression)

        # otherwise we have an error, there must be an expression here
        self.ast_error(f"expected an expression, found '{self.current()}'!")

    def identifier_expression(self, token: IdentifierToken) -> Expression:
        expression: IdentifierExpression = IdentifierExpression(token.source_location, token)

        # check for increment and decrement
        if increment_token := self.match(TokenType.INCREMENT):
            source_location: SourceLocation = expression.source_location + increment_token.source_location
            return UnaryExpression(source_location, ExpressionType.POST_INCREMENT, expression)
        if decrement_token := self.match(TokenType.DECREMENT):
            source_location: SourceLocation = expression.source_location + decrement_token.source_location
            return UnaryExpression(source_location, ExpressionType.POST_DECREMENT, expression)

        # check for a function call
        if self.match(TokenType.PAREN_OPEN):
            return self.call_expression(expression)

        # check for a dot
        if self.match(TokenType.DOT):
            inner_token: Token = self.expect(TokenType.IDENTIFIER)
            assert isinstance(inner_token, IdentifierToken)
            expression.inner_expression = self.identifier_expression(inner_token)

        # otherwise return the bare token expression
        return expression

    def call_expression(self, identifier_expression: IdentifierExpression) -> CallExpression:
        # the identifier expression is provided, and the opening parenthesis is consumed

        # check for a closing parenthesis, then we have a function call without arguments
        if paren_close := self.match(TokenType.PAREN_CLOSE):
            # calculate the SourceLocation from (outer) identifier expression till paren_close
            source_location: SourceLocation = identifier_expression.source_location + paren_close.source_location
            # simply return a call expression without arguments
            return CallExpression(source_location, identifier_expression, self._class_type)

        # otherwise start parsing the arguments
        arguments: list[Expression] = []
        while True:
            # start with the expression
            expression: Expression = self.expression()
            arguments.append(expression)

            # if we don't have a comma, it's the end of the argument list
            if not self.match(TokenType.COMMA):
                break

        # we must end with a closing parenthesis
        paren_close = self.expect(TokenType.PAREN_CLOSE)

        # calculate the SourceLocation from (outer) identifier expression till paren_close and everything in between
        source_location: SourceLocation = identifier_expression.source_location + paren_close.source_location

        # construct and return the call expression
        return CallExpression(source_location, identifier_expression, self._class_type, arguments)

    def ast_error(self, message: str) -> NoReturn:
        """constructs and raises an AstError"""
        # extract the line number from the current or previous token
        source_location: SourceLocation | None = None
        try:
            # try to get the SourceLocation from the current token
            source_location: SourceLocation | None = self.current().source_location
        except IndexError:
            # if that fails (out of bounds), try the previous token
            if self._current_index != 0:  # sanity check for previous()
                source_location: SourceLocation | None = self.previous().source_location

        raise AstError(message, self._filename, source_location)

    def generate(self) -> AST:
        """parses the token stream to a list of statements, until EOF is reached"""
        errors: list[TaplError] = []
        ast: AST = AST(self._filename, self._types)
        while not self.is_at_end():
            try:
                ast.append(self.statement())
            except TaplError as e:
                errors.append(e)
                # continue until we get to a newline, indicating a new statement
                while not self.match(TokenType.NEWLINE, TokenType.EOF):
                    self.consume()
                # check if we have consumed the EOF, then don't check for indent/dedent
                if self.is_at_end():
                    break
                # also consume the indent and dedent tokens if they are there
                while self.match(TokenType.INDENT, TokenType.DEDENT):
                    pass

        # if we found errors, print them and exit with exit code 1
        if errors:
            [print(e) for e in errors]
            exit(1)

        return ast
