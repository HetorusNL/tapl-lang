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
    def __init__(self):
        self.modules: dict[str, Module] = {}

    def modularize(self, folder: Path, prefix: str) -> list[ModuleError]:
        # make sure we are modularizing a folder, not a file
        assert folder.is_dir(), f"Expected a folder, got {folder}"

        module_errors: list[ModuleError] = []

        # loop through the objects in the folder
        for obj in folder.iterdir():
            # if the object is a folder, modularize it recursively
            if obj.is_dir():
                self.modularize(obj, f"{prefix}.{obj.name}")
                continue

            # if the object is not a .tim file, ignore it
            if obj.suffix != ".tim":
                continue

            # parse the .tim file and check if the naming is correct
            try:
                module_file = self._modularize(obj)
            except ModuleError as e:
                # in case of an error, add it to the errors list and continue with the next file
                module_errors.append(e)
                continue

            module_name: str = module_file.name
            if module_name != "main" and not module_name.startswith(prefix):
                # misformed module name, add it to the errors list and continue with the next file
                message: str = f"module name misformed, '{module_name}' doesn't start with '{prefix}.'!"
                module_errors.append(ModuleError(message, obj, module_file.source_location))
                continue

            # add it to the module map or append the ModuleFile if the module_name already exists
            if module_name in self.modules:
                self.modules[module_name].module_files.append(module_file)
            else:
                self.modules[module_name] = Module(module_name, module_file)

        # return the collected module errors, if any
        return module_errors

    def _modularize(self, filename: Path) -> ModuleFile:
        tokens: Stream[Token] = self._tokenize_file(filename)
        module_file: ModuleFile = self._parse_stream(filename, tokens)
        return module_file

    def _tokenize_file(self, filename: Path) -> Stream[Token]:
        print(f"calling the tokenizer with file '{filename}'")
        tokens: Stream[Token] = Tokenizer(filename).tokenize()
        return tokens

    def _parse_stream(self, filename: Path, tokens: Stream[Token]) -> ModuleFile:
        name: str | None = None
        source_location: SourceLocation | None = None
        imports: list[str] = []
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
                    # found the 'import' token, now parse the name
                    labels = self._get_dot_separated_name(filename, tokens)
                    imports.append(".".join(label.value for label in labels))
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

        return ModuleFile(name, source_location, filename, imports, tokens)

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
