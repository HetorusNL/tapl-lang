#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path

from ..errors.module_error import ModuleError
from .module import Module
from .module_file import ModuleFile
from .stream import Stream
from .stream import StreamError
from ..tokenizer import Tokenizer
from ..tokens.identifier_token import IdentifierToken
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from .source_location import SourceLocation


class ModuleMap:
    def __init__(self, main_file: Path):
        self.modules: dict[str, Module] = {}
        self.module_errors: list[ModuleError] = []
        self.main_file: Path = main_file
        self.containing_folder: Path = self.main_file.parent
        self.prefix: str = self.containing_folder.name

    def modularize(self) -> list[ModuleError]:
        # sanity check that the provided file is a file
        if not self.main_file.is_file():
            return [ModuleError(f"file '{self.main_file}' does not exist!", self.main_file, None)]

        # TODO: only modularize the provided file, and resolved import folders
        self._modularize(self.containing_folder, self.prefix)

        # parse the raw_imports from ModuleFile objects to imports on Module level
        self._parse_raw_imports()

        # return the collected module errors, if any
        return self.module_errors

    def _modularize(self, folder: Path, prefix: str) -> None:
        # loop through the objects in the folder
        for obj in folder.iterdir():
            # if the object is a folder, modularize it recursively
            if obj.is_dir():
                self._modularize(obj, f"{prefix}.{obj.name}")
                continue

            # if the object is not a .tim file, ignore it
            if obj.suffix != ".tim":
                continue

            # parse the .tim file and check if the naming is correct
            try:
                module_file = self._modularize_file(obj)
            except ModuleError as e:
                # in case of an error, add it to the errors list and continue with the next file
                self.module_errors.append(e)
                continue

            # check that the module name is correct
            if not self._check_name(module_file, prefix):
                # _check_name already added the error, continue with the next file
                continue

            # add it to the module map or append the ModuleFile if the module_name already exists
            module_name: str = module_file.name
            if module_name in self.modules:
                self.modules[module_name].module_files.append(module_file)
            else:
                self.modules[module_name] = Module(module_name, module_file)

    def _modularize_file(self, filename: Path) -> ModuleFile:
        tokens: Stream[Token] = self._tokenize_file(filename)
        module_file: ModuleFile = self._parse_stream(filename, tokens)
        return module_file

    def _tokenize_file(self, filename: Path) -> Stream[Token]:
        tokens: Stream[Token] = Tokenizer(filename).tokenize()
        # print(tokens.objects)
        return tokens

    def _parse_stream(self, filename: Path, tokens: Stream[Token]) -> ModuleFile:
        name: str | None = None
        source_location: SourceLocation | None = None
        raw_imports: list[tuple[str, SourceLocation]] = []
        try:
            for token in tokens.iter():
                if token.token_type == TokenType.MODULE:
                    source_location = token.source_location
                    # found the 'module' token, now parse the name
                    if name is not None:
                        raise ModuleError("there can only be one module name!", filename, token.source_location)
                    labels = self._get_dot_separated_name(filename, tokens)
                    for label in labels:
                        source_location += label.source_location
                    name = ".".join(label.value for label in labels)
                if token.token_type == TokenType.IMPORT:
                    source_location = token.source_location
                    # found the 'import' token, now parse the name
                    labels = self._get_dot_separated_name(filename, tokens)
                    for label in labels:
                        source_location += label.source_location
                    import_name: str = ".".join(label.value for label in labels)
                    raw_import = (import_name, source_location)
                    raw_imports.append(raw_import)
        except StreamError:
            # iterating past the end of the stream, invalid code: don't care
            pass

        if name is None or source_location is None:
            message: str = f"file has no module name!"
            if tokens.objects:
                # add the SourceLocation of the first token, as module should be on top of the file
                raise ModuleError(message, filename, tokens.objects[0].source_location)
            # no tokens in the file, add no SourceLocation
            raise ModuleError(message, filename, None)

        return ModuleFile(name, source_location, filename, raw_imports, tokens)

    def _get_dot_separated_name(self, filename: Path, tokens: Stream[Token]) -> list[IdentifierToken]:
        labels: list[IdentifierToken] = []
        offset: int = 0
        while True:
            # extract the (next) label of the module name
            identifier: Token = tokens.iter_next(offset)
            offset += 1
            if isinstance(identifier, IdentifierToken):
                # add the label to the list
                labels.append(identifier)
            else:
                # we found something else than an IdentifierToken, this is an error
                message: str = f"expected a '.' separated module name, found '{identifier}'!"
                raise ModuleError(message, filename, identifier.source_location)

            # check if we have a dot, then we continue otherwise break from the loop
            next_token: Token = tokens.iter_next(offset)
            offset += 1
            if next_token.token_type != TokenType.DOT:
                break

        # return the full module name as determined above
        return labels

    def _check_name(self, module_file: ModuleFile, prefix: str) -> bool:
        filename: Path = module_file.filename
        module_name: str = module_file.name

        if filename.samefile(self.main_file):
            if module_name != "main":
                # misformed main module name, add it to the errors list and return False
                message: str = f"main module name misformed, '{module_name}' is not 'main'!"
                self.module_errors.append(ModuleError(message, filename, module_file.source_location))
                return False
        else:
            if not module_name.startswith(prefix):
                # misformed module name, add it to the errors list and return False
                message: str = f"module name misformed, '{module_name}' doesn't start with '{prefix}.'!"
                self.module_errors.append(ModuleError(message, filename, module_file.source_location))
                return False

        return True

    def _parse_raw_imports(self) -> None:
        for module in self.modules.values():
            for module_file in module.module_files:
                for module_name, source_location in module_file.raw_imports:
                    # get the module from the modules dict
                    module_import: Module | None = self.modules.get(module_name)

                    # verify that the module is found
                    if not module_import:
                        message: str = f"module '{module_name}' not found!"
                        self.module_errors.append(ModuleError(message, module_file.filename, source_location))
                        continue

                    # add the import to the module imports if not already there
                    if module_import not in module.imports:
                        module.imports.append(module_import)
