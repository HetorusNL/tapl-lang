#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.ast_checks.scoping_pass import ScopingPass
from compyler.ast_checks.typing_pass import TypingPass
from compyler.utils.ast_collection import AstCollection


class AstCheck:
    def __init__(self, ast_collection: AstCollection):
        self._ast_collection: AstCollection = ast_collection

    def run(self) -> None:
        """run several passes on the AST to perform a variety of checks on the statements"""
        scoping_pass: ScopingPass = ScopingPass(self._ast_collection)
        typing_pass: TypingPass = TypingPass(self._ast_collection)

        # check the variables defined in the scopes of the AST
        scoping_pass.run()

        # check and apply types to the variables, including type 'upscaling'
        typing_pass.run()
        # check that all expressions have a type
        typing_pass.verify_types()
