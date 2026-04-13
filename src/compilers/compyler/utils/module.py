#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .module_file import ModuleFile


class Module:
    def __init__(self, name: str, module_file: ModuleFile):
        self.name: str = name
        self.module_files: list[ModuleFile] = [module_file]
        self.imports: list[Module] = []
