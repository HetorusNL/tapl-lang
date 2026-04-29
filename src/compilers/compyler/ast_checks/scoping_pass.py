#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .pass_base import PassBase
from ..utils.ast_collection import AstCollection
from ..visitors.scoping_pass_expression_visitor import ScopingPassExpressionVisitor
from ..visitors.scoping_pass_statement_visitor import ScopingPassStatementVisitor


class ScopingPass(PassBase[None]):
    def __init__(self, ast_collection: AstCollection):
        # create the visitors of the ScopingPass and pass them to the PassBase
        expression_visitor = ScopingPassExpressionVisitor(self)
        statement_visitor = ScopingPassStatementVisitor(self)
        super().__init__(ast_collection, expression_visitor, statement_visitor)
