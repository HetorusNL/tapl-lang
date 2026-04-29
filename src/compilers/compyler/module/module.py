#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from collections.abc import Iterator

from .module_file import ModuleFile
from .raw_import import RawImport
from ..types.types import Types


class Module:
    def __init__(self, name: str, module_file: ModuleFile):
        self.name: str = name
        self.module_files: list[ModuleFile] = [module_file]
        self.imports: list[Module] = []
        self.types: Types | None = None
        self.processing_started: bool = False
        self.types_processed: bool = False
        self.ast_generated: bool = False

    @property
    def processed(self) -> bool:
        return self.types_processed and self.ast_generated

    @property
    def raw_imports(self) -> Iterator[RawImport]:
        for module_file in self.module_files:
            for raw_import in module_file.raw_imports:
                yield raw_import
