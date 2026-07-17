#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path
import unittest

from compyler.ast_generator import AstGenerator
from compyler.ast_checks.ast_check import AstCheck
from compyler.backends.c_backend_expression_visitor import CBackendExpressionVisitor
from compyler.backends.c_backend_state import CBackendState
from compyler.backends.c_backend_statement_visitor import CBackendStatementVisitor
from compyler.expressions.call_expression import CallExpression
from compyler.expressions.identifier_expression import IdentifierExpression
from compyler.statements.statement import Statement
from compyler.tokenizer import Tokenizer
from compyler.tokens.identifier_token import IdentifierToken
from compyler.tokens.token import Token
from compyler.types.type_applier import TypeApplier
from compyler.types.type_resolver import TypeResolver
from compyler.types.types import Types
from compyler.utils.ast import AST
from compyler.utils.ast_collection import AstCollection
from compyler.utils.source_location import SourceLocation
from compyler.utils.stream import Stream


class TestAstGenerator(unittest.TestCase):
    def setUp(self):
        print()

    def test_ast_generator_example_statements(self):
        self._run_compilation_test("example_statements.tim", "result_example_statements.txt")

    def test_ast_generator_indentation_tests(self):
        self._run_compilation_test("indentation_tests.tim", "result_indentation_tests.txt")

    def test_ast_generator_for_statement(self):
        self._run_compilation_test("for_loop_statements.tim", "result_for_loop_statements.txt")

    def test_ast_generator_functions(self):
        self._run_compilation_test("functions.tim", "result_functions.txt")

    def test_list_identifier_is_emitted_as_pointer_for_function_calls(self):
        state = CBackendState()
        expression_visitor = CBackendExpressionVisitor(state)
        source_location = SourceLocation(0, 0)

        list_type = Types().add_list_type(Types()["char"])
        identifier_token = IdentifierToken(source_location, "buffer")
        argument_expression = IdentifierExpression(source_location, identifier_token)
        argument_expression.type_ = list_type
        argument_expression.list_type = list_type

        function_identifier = IdentifierExpression(source_location, IdentifierToken(source_location, "read_file"))
        expression = CallExpression(source_location, function_identifier, None, [argument_expression])
        expression.type_ = Types()["bool"]

        self.assertEqual(expression.accept(expression_visitor), "read_file(&buffer)")

    def _run_compilation_test(self, tim_file: str, result_statements_file: str):
        # make sure to pass a resolved path to the tokenizer and ast generator
        this_folder: Path = Path(__file__).parent.resolve()
        example_file: Path = this_folder / tim_file
        # tokenize the file to a stream
        tokens: Stream[Token] = Tokenizer(example_file).tokenize()
        # resolve the types in the file
        type_resolver: TypeResolver = TypeResolver(tokens)
        types: Types = type_resolver.resolve()
        # apply the types to the tokens in the stream
        type_applier: TypeApplier = TypeApplier(example_file, types)
        type_applier.apply(tokens)
        # generate the ast and resulting statements to verify
        ast_generator: AstGenerator = AstGenerator(example_file, tokens, types).generate()
        ast: AST = ast_generator.ast
        ast_collection: AstCollection = AstCollection()
        ast_collection.append(ast)
        AstCheck(ast_collection).run()
        ast_statements: list[Statement] = ast.statements.objects
        print(*ast_statements, sep="\n")

        # convert the individual statements to str to compare
        result_file: Path = this_folder / result_statements_file
        with open(result_file) as f:
            result: list[str] = f.readlines()
        # create the state and the visitors for the C backend
        state = CBackendState()
        expression_visitor = CBackendExpressionVisitor(state)
        statement_visitor = CBackendStatementVisitor(state, expression_visitor)
        # convert code lines to single lines and strip newlines
        main_code_lines: list[str] = []
        for statement in ast_statements:
            if code := statement.accept(statement_visitor):
                main_code_lines.append(code)
        # add the function declarations and definitions as well
        code_lines: list[str] = []
        for line in state.function_declarations:
            code_lines.extend(l.strip() for l in line.strip().split("\n"))
        for line in state.function_definitions:
            code_lines.extend(l.strip() for l in line.strip().split("\n"))
        for line in main_code_lines:
            code_lines.extend(l.strip() for l in line.strip().split("\n"))
        # do the same for the result lines
        result_lines: list[str] = [line.strip() for line in result]
        # check that the lists are equal
        self.assertEqual(code_lines, result_lines)
