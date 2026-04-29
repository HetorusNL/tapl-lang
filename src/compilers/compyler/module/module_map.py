#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path

from ..errors.module_error import ModuleError
from .modularize_folder import ModularizeFolder
from .module import Module
from .raw_import import RawImport
from .module_file import ModuleFile
from ..utils.stream import Stream
from ..utils.stream import StreamError
from ..tokenizer import Tokenizer
from ..tokens.identifier_token import IdentifierToken
from ..tokens.token import Token
from ..tokens.token_type import TokenType
from ..utils.source_location import SourceLocation


class ModuleMap:
    def __init__(self, main_file: Path):
        # objects to store the modules and errors found during modularization
        self.modules: dict[str, Module] = {}
        self.module_errors: list[ModuleError] = []

        # store the main_file and properties related to the main file in the class
        self.main_file: Path = main_file
        self.containing_folder: Path = self.main_file.parent
        self.prefix: str = self.containing_folder.name
        self.parent_folder: Path = self.containing_folder.parent

        # store the remaining folders to modularize and already modularized folders and files
        self._remaining_folders: list[ModularizeFolder] = []
        self._modularized_folders: list[ModularizeFolder] = []
        self._modularized_files: list[Path] = []

    def modularize(self) -> list[ModuleError]:
        # sanity check that the provided file is a file
        if not self.main_file.is_file():
            return [ModuleError(f"file '{self.main_file}' does not exist!", self.main_file, None)]

        # start by modularizing the main file
        self._modularize_file(self.main_file, self.prefix)

        # while there are remaining_folders to modularize, modularize the next one
        while self._remaining_folders:
            folder = self._remaining_folders.pop()
            self._modularized_folders.append(folder)
            self._modularize_folder(folder)

        # parse the raw_imports from ModuleFile objects to imports on Module level
        self._parse_raw_imports()

        # return the collected module errors, if any
        return self.module_errors

    def _modularize_folder(self, folder: ModularizeFolder) -> None:
        print(f'modularizing folder "{folder.name}" with prefix "{folder.prefix}"')
        # loop through the objects in the folder
        for obj in folder.name.iterdir():
            # don't recursively modularize folders, only when explicitly imported
            if obj.is_dir():
                continue

            # if the object is not a .tim file, ignore it
            if obj.suffix != ".tim":
                continue

            self._modularize_file(obj, folder.prefix)

    def _modularize_file(self, filename: Path, prefix: str) -> None:
        print(f'modularizing file "{filename}" with prefix "{prefix}"')

        # check if the file is already modularized, if so ignore it
        if filename in self._modularized_files:
            return

        # add the file to the modularized files, so we don't modularize it again
        self._modularized_files.append(filename)

        # parse the .tim file and check if the naming is correct
        try:
            module_file = self._create_module_file(filename)
        except ModuleError as e:
            # in case of an error, add it to the errors list and continue with the next file
            self.module_errors.append(e)
            return

        # check that the module name is correct
        if not self._check_name(module_file, prefix):
            # _check_name already added the error (if applicable), continue with the next file
            return

        # add it to the module map or append the ModuleFile if the module_name already exists
        module_name: str = module_file.name
        if module_name in self.modules:
            self.modules[module_name].module_files.append(module_file)
        else:
            self.modules[module_name] = Module(module_name, module_file)

        # check the imports of the file, and add non-existing ones to the remaining folders
        for raw_import in module_file.raw_imports:
            self._check_module_import(raw_import)

    def _create_module_file(self, filename: Path) -> ModuleFile:
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
        raw_imports: list[RawImport] = []
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
                    raw_import = RawImport(import_name, filename, source_location)
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
                message: str = f"expected a dot-separated module name, found '{identifier}'!"
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
            if module_name == "main":
                # silently ignore main modules for other files, as they are not the main_file provided to the compiler
                return False
            if not module_name.startswith(prefix):
                # misformed module name, add it to the errors list and return False
                message: str = f"module name misformed, '{module_name}' doesn't start with '{prefix}.'!"
                self.module_errors.append(ModuleError(message, filename, module_file.source_location))
                return False

        return True

    def _check_module_import(self, raw_import: RawImport) -> None:
        # extract the folder name from the import name, everthing except the last segment
        import_name_segments: list[str] = raw_import.name.split(".")[:-1]

        # if there are no segments, the import is misformed, so ignore it
        if not import_name_segments:
            message: str = f"import name '{raw_import.name}' is misformed, "
            message += f"it should be a dot separated name from main module's parent folder!"
            self.module_errors.append(ModuleError(message, raw_import.filename, raw_import.source_location))
            return

        # construct the folder name from the parent folder and segments
        folder_name: Path = self.parent_folder
        for segment in import_name_segments:
            folder_name /= segment

        # sanity check that the folder is in fact a folder
        if not folder_name.is_dir():
            return

        folder_prefix: str = ".".join(import_name_segments)
        new_folder: ModularizeFolder = ModularizeFolder(folder_name, folder_prefix)
        # check that the folder is not already modularized or in the remaining folders
        if new_folder not in self._modularized_folders and new_folder not in self._remaining_folders:
            # if not add it to the remaining folders
            self._remaining_folders.append(new_folder)

    def _parse_raw_imports(self) -> None:
        for module in self.modules.values():
            for raw_import in module.raw_imports:
                # get the module from the modules dict
                module_import: Module | None = self.modules.get(raw_import.name)

                # verify that the module is found
                if not module_import:
                    filename: Path = raw_import.filename
                    source_location: SourceLocation = raw_import.source_location
                    message: str = f"module '{raw_import.name}' not found in '{self.parent_folder}'!"
                    self.module_errors.append(ModuleError(message, filename, source_location))
                    continue

                # add the import to the module imports if not already there
                if module_import not in module.imports:
                    module.imports.append(module_import)
