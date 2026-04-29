#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .ast import AST


class AstCollection:
    def __init__(self):
        # the AstCollection consists of a list of ASTs to be processed in sequence
        self.asts: list[AST] = []

    def append(self, ast: AST) -> None:
        self.asts.append(ast)

    def iter(self):
        """returns an iterator over the statements of the ASTs in the collection, in sequence"""
        for ast in self.asts:
            for statement in ast.statements.iter():
                yield statement
