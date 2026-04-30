#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

import argparse
from pathlib import Path
from subprocess import CalledProcessError
from subprocess import CompletedProcess
from subprocess import run
from typing import NoReturn

from .ast_checks.ast_check import AstCheck
from .utils.ast_collection import AstCollection
from .ast_generator import AstGenerator
from .backends.c_backend_code_generator import CBackendCodeGenerator
from .errors.typing_error import TypingError
from .tokens.token import Token
from .types.class_type import ClassType
from .types.type_applier import TypeApplier
from .types.type_resolver import TypeResolver
from .types.types import Types
from .utils.ast import AST
from .module.module import Module
from .module.module_file import ModuleFile
from .module.module_map import ModuleMap
from .utils.stream import Stream


class Compyler:
    # construct several path constants for the files and folders used in the Compyler
    repo_root: Path = Path(__file__).parents[3].resolve()
    stdlib_folder: Path = repo_root / "src" / "stdlib"
    templates_folder: Path = repo_root / "src" / "templates"
    build_folder: Path = repo_root / "build" / "compyler"
    header_folder: Path = build_folder / "tapl_headers"

    def __init__(self) -> None:
        self.typing_errors: list[TypingError] = []
        self.class_types: dict[str, ClassType] = {}
        self.ast_collection: AstCollection = AstCollection()

    def _argument_parser(self) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("file")
        hurry_help: str = "hurry up the compilation process, resulting in less human readable generated code"
        parser.add_argument("--hurry", action="store_true", help=hurry_help)
        parsed_args = parser.parse_args()

        # stored the parsed arguments in the class
        self.args_hurry = parsed_args.hurry
        self.args_file = Path(parsed_args.file)

    def _modularize(self) -> ModuleMap:
        module_map: ModuleMap = ModuleMap(self.args_file)

        # recursively modularize the folder of the provided file
        if module_errors := module_map.modularize():
            [print(e) for e in module_errors]
            exit(1)

        return module_map

    def _process_modules(self, module_map: ModuleMap) -> None:
        # get the main module from the map to start processing
        main_module = module_map.modules["main"]

        # recursively process from the leaves until the main module itself
        self._process_module(main_module)

        # if there are any typing errors, print them and exit with failure
        if self.typing_errors:
            [print(e) for e in self.typing_errors]
            exit(1)

    def _process_module(self, module: Module) -> None:
        # if the module is already processed, return early
        if module.processed:
            return

        # if the module is already being processed we have a circular import, which we don't support
        if module.processing_started:
            message: str = f"circular import detected for module '{module.name}'!"
            # simply add the first modulefile here, as there is at least one
            self.typing_errors.append(TypingError(message, module.module_files[0].filename))
            return

        # mark the module as being processed
        module.processing_started = True

        # recursively process the imported modules first
        for module_import in module.imports:
            # TODO: actually the class types should not be shared between imports
            self._process_module(module_import)

        # apply the two typing passes to the token stream of the module
        self._typing_passes(module)

        # mark the module as having its types processed
        module.types_processed = True

        # generate the ast for the module files and add it to the AstCollection
        # TODO: the module files should be merged before generating the AST, but for now we process them in sequence
        for module_file in module.module_files:
            assert module.types is not None
            ast: AST = self._generate_ast(module_file, module.types)
            self.ast_collection.append(ast)

        # mark the module as AST generated
        module.ast_generated = True

    def _typing_passes(self, module: Module) -> None:
        # first resolve all types in the token stream
        for module_file in module.module_files:
            # resolve the types in the file
            type_resolver: TypeResolver = TypeResolver(module_file.tokens)
            types: Types = type_resolver.resolve()

            # add the resolved class types in the map to use in the type applier pass
            for class_type in types.class_types.values():
                # check if a class with the same name is already defined
                if class_type.keyword in self.class_types:
                    message: str = f"class '{class_type.keyword}' is already defined!"
                    self.typing_errors.append(TypingError(message, module_file.filename))
                    continue

                # otherwise add the class type to the map
                self.class_types[class_type.keyword] = class_type

        # construct a full types object for the type applier pass, with all resolved classes
        module.types = Types()
        module.types.class_types.update(self.class_types)

        # then apply the resolved types to the token stream (in place)
        for module_file in module.module_files:
            type_applier: TypeApplier = TypeApplier(module_file.filename, module.types)
            type_applier.apply(module_file.tokens)

    def _generate_ast(self, module_file: ModuleFile, types: Types) -> AST:
        # run the AST generator
        filename: Path = module_file.filename
        tokens: Stream[Token] = module_file.tokens
        ast_generator: AstGenerator = AstGenerator(filename, tokens, types).generate()

        # get the AST from the generator and return it
        ast: AST = ast_generator.ast
        print(*ast.statements.objects, sep="\n")
        return ast

    def _check_ast_collection(self) -> None:
        """run several checks on the generated AstCollection"""
        AstCheck(self.ast_collection).run()

    def _create_build_folders(self) -> None:
        # ensure the build and header folders exists
        self.build_folder.mkdir(parents=True, exist_ok=True)
        self.header_folder.mkdir(parents=True, exist_ok=True)

    def _generate_code(self, ast_collection: AstCollection) -> Path:
        # the new visitor pattern code generator for whole AstCollections
        generator = CBackendCodeGenerator(ast_collection, self.build_folder, self.header_folder, self.templates_folder)
        generator.generate()
        return generator.get_main_file()

    def _copy_stdlib(self) -> None:
        # recursively copy all header files to the header folder
        # using the neat Path.copy_into function, available since python 3.14
        for header in self.stdlib_folder.glob("*.h"):
            header.copy_into(self.header_folder)

    def _format_files(self) -> None:
        # recursively find all .c and .h files in the build folder and format all found files
        for file_path in self.build_folder.rglob("*.[ch]"):
            if file_path.is_file():
                command: list[str] = ["clang-format", "-i", "--fallback-style=none", str(file_path)]
                returncode: int = self._execute_command(command).returncode
                if returncode != 0:
                    self.handle_error(f"clang-format failed to format {file_path} with error code {returncode}")

    def _compile_c(self, c_file: Path) -> Path:
        executable: Path = c_file.parent / "main"

        # remove the old executable (if it exists)
        command: list[str] = ["rm", "-f", str(executable)]
        self._execute_command(command)

        # directly call the gcc compiler, passing the build folder as additional include path
        command: list[str] = ["gcc", "-O0", "-g3", f"-I{self.build_folder}", "-o", str(executable), str(c_file)]
        returncode: int = self._execute_command(command).returncode
        if returncode != 0:
            self.handle_error(f"gcc returned error code {returncode}")
        return executable

    def _run_executable(self, executable: Path) -> None:
        command: list[str] = [str(executable)]
        returncode: int = self._execute_command(command).returncode
        if returncode != 0:
            self.handle_error(f"executable returned error code {returncode}")

    def _execute_command(self, command: list[str]) -> CompletedProcess[bytes]:
        """print and execute a command and return its result"""
        print(" ".join(command))
        try:
            result = run(command)
            return result
        except CalledProcessError as e:
            self.handle_error(f"command '{' '.join(command)}' failed with error code {e.returncode}")
        except FileNotFoundError:
            self.handle_error(f"command '{command[0]}' not found")

    def handle_error(self, error_msg: str) -> NoReturn:
        # lazy import the inspect and colors modules for error handling
        import inspect
        from inspect import FrameInfo

        from .utils.colors import Colors

        # try to get the line number of the function calling this function
        stack: list[FrameInfo] = inspect.stack()
        line: str = f"{stack[1].lineno}:" if len(stack) >= 2 else ""

        # construct the filename and error message with colors
        filename: str = f"\n{Colors.BOLD}{__file__}:{line} {Colors.RESET}"
        error: str = f"{Colors.BOLD}{Colors.RED}internal compiler error: {Colors.RESET}"

        # print the error and exit with failure
        print(f"{filename}{error}{error_msg}!")
        print(f"{Colors.BOLD}{Colors.MAGENTA}terminating...{Colors.RESET}")
        exit(1)

    def compile(self) -> Path:
        # get the 'file' argument from the argument parser
        self._argument_parser()

        # modularize the main and imported files
        module_map: ModuleMap = self._modularize()

        # process the tree of modules to resolve the types and generate the AstCollection
        self._process_modules(module_map)

        # run several checks on the generated AstCollection
        self._check_ast_collection()

        # formulate the path to output the c-code, and a subfolder for the headers
        self._create_build_folders()

        # generate c-code from the AST and write the source files in the build folder
        c_file: Path = self._generate_code(self.ast_collection)

        # copy the files in the standard library to the header folder
        self._copy_stdlib()

        # format the generated c-code files
        if not self.args_hurry:
            self._format_files()

        # run the c compiler to compile the file
        executable: Path = self._compile_c(c_file)

        # return the path to the executable
        return executable

    def run(self, executable: Path) -> None:
        # run the executable
        self._run_executable(executable)


if __name__ == "__main__":
    compyler: Compyler = Compyler()
    executable: Path = compyler.compile()
    compyler.run(executable)
