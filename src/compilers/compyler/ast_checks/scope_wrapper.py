#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.ast_checks.scope import Scope


class ScopeWrapper:
    def __init__(self):
        self.scope: Scope = Scope()

    @property
    def empty(self) -> bool:
        return self.scope.empty

    def add_scope(self) -> None:
        self.scope = Scope(self.scope)

    def remove_scope(self) -> None:
        assert self.scope.parent is not None, "internal compiler error, trying to leave innermost scope!"
        self.scope = self.scope.parent
