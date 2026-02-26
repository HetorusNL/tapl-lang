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
from ..expressions.expression import Expression
from ..statements.statement import Statement
from ..tokens.identifier_token import IdentifierToken
from ..types.type import Type
from ..utils.ast import AST
from ..utils.source_location import SourceLocation
from .scope_wrapper import ScopeWrapper

from ..visitors.base_expression_visitor import BaseExpressionVisitor
from ..visitors.base_statement_visitor import BaseStatementVisitor


class PassBase[T]:
    """Base class of AST check passes, with the common functionality"""

    def __init__(
        self,
        ast: AST,
        expression_visitor: BaseExpressionVisitor[T],
        statement_visitor: BaseStatementVisitor[T],
    ):

        self._ast: AST = ast
        # store a linked list of scopes inside a wrapper that stores the functions and variables
        self.scope_wrapper: ScopeWrapper = ScopeWrapper()
        # also create a scope stash to move the scope aside for a clean one
        self._scope_wrapper_stash: ScopeWrapper = ScopeWrapper()
        # store a list of errors during this pass, if they occur
        self._errors: list[TaplError] = []
        # store the visitors
        self.expression_visitor: BaseExpressionVisitor[T] = expression_visitor
        self.statement_visitor: BaseStatementVisitor[T] = statement_visitor

    def run(self) -> None:
        for statement in self._ast.statements.iter():
            self.parse_statement(statement)

        # ensure that we have the global scope and only the global scope left
        error: str = f"internal compiler error"
        assert self.scope_wrapper.scope.parent is None, f"{error}, more scopes than the global scope left!"
        # ensure that we have no scope stash left
        assert self._scope_wrapper_stash.empty, f"{error}, scope stash is not empty!"

        # if we found errors, print them and exit with exit code 1
        if self._errors:
            [print(e) for e in self._errors]
            exit(1)

    def parse_statement(self, statement: Statement | None) -> T | None:
        """wrapper around the statement parsing to catch and handle exceptions"""
        try:
            if statement:
                return statement.accept(self.statement_visitor)
        except TaplError as e:
            self._errors.append(e)

    def parse_expression(self, expression: Expression | None) -> T | None:
        """wrapper around the expression parsing to catch and handle exceptions"""
        try:
            if expression:
                return expression.accept(self.expression_visitor)
        except TaplError as e:
            self._errors.append(e)

    def add_identifier(self, identifier_token: IdentifierToken, type_: Type):
        """first checks if the identifier already exists in innermost scope, otherwise adds identifier"""
        identifier: str = identifier_token.value
        # check in the innermost scope if the identifier already exists
        if identifier in self.scope_wrapper.scope.identifiers:
            self.ast_error(f"identifier '{identifier}' already exists!", identifier_token.source_location)

        # otherwise add the identifier in the innermost scope
        self.scope_wrapper.scope.add_identifier(identifier, type_)

    def get_identifier_type(self, identifier_token: IdentifierToken) -> Type:
        """checks that the identifier exists in current or inner scopes, and return its type"""
        identifier: str = identifier_token.value
        if type_ := self.scope_wrapper.scope.get_identifier(identifier):
            return type_

        # the identifier doesn't exist, raise an error
        self.ast_error(f"unknown identifier '{identifier}'!", identifier_token.source_location)

    @contextmanager
    def new_scope(self) -> Generator[None]:
        """enter a new outer scope for the content in the 'with' statement"""
        try:
            # first enter the scope by adding a new outer scope
            self.scope_wrapper.add_scope()
            # then give control to the caller
            yield
        finally:
            # no matter if there is an exception, leave the outer scope
            print(f"leaving scope with identifiers: {{{', '.join(self.scope_wrapper.scope.identifiers.keys())}}}")
            self.scope_wrapper.remove_scope()

    @contextmanager
    def clean_scope(self) -> Generator[ScopeWrapper]:
        """create a new clean scope for the content in the 'with' statement"""
        try:
            # make sure the scope stash is currently empty
            assert self._scope_wrapper_stash.empty, "internal compiler error, clean scope already active!"
            # move the scope to the stash and create an empty scope list
            self._scope_wrapper_stash: ScopeWrapper = self.scope_wrapper
            self.scope_wrapper: ScopeWrapper = ScopeWrapper()
            # then give control to the caller
            yield self.scope_wrapper
        finally:
            # no matter if there is an exception, restore the scope from the stash
            # create a reference to the clean scope to return
            clean_scope: ScopeWrapper = self.scope_wrapper
            # restore the scope from the stash
            assert not self._scope_wrapper_stash.empty, "internal compiler error, no scope stash found!"
            self.scope_wrapper: ScopeWrapper = self._scope_wrapper_stash
            # create a new empty scope stash
            self._scope_wrapper_stash = ScopeWrapper()
            print(f"returning scope with identifiers: {{{', '.join(clean_scope.scope.all_identifiers)}}}")

    def ast_error(self, message: str, source_location: SourceLocation) -> NoReturn:
        """constructs and raises an AStError"""
        raise AstError(message, self._ast.filename, source_location)
