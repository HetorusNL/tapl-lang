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
from .ast_generator import AstGenerator
from .backends.c_backend_code_generator import CBackendCodeGenerator
from .tokens.token import Token
from .types.type_applier import TypeApplier
from .types.type_resolver import TypeResolver
from .types.types import Types
from .utils.ast import AST
from .module.module_map import ModuleMap
from .utils.stream import Stream


# get to the repo root folder, several levels up
repo_root: Path = Path(__file__).parents[3].resolve()
stdlib_folder: Path = repo_root / "src" / "stdlib"
templates_folder: Path = repo_root / "src" / "templates"


def argument_parser() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parsed_args = parser.parse_args()
    return Path(parsed_args.file)


def modularize(file: Path) -> ModuleMap:
    module_map: ModuleMap = ModuleMap(file)

    # recursively modularize the folder of the provided file
    if module_errors := module_map.modularize():
        [print(e) for e in module_errors]
        exit(1)

    return module_map


def typing_passes(filename: Path, tokens: Stream[Token]) -> Types:
    # resolve the types in the file
    type_resolver: TypeResolver = TypeResolver(tokens)
    types: Types = type_resolver.resolve()
    # apply the types to the tokens in the stream (in place)
    type_applier: TypeApplier = TypeApplier(filename, types)
    type_applier.apply(tokens)
    # return the processed tokens
    return types


def generate_ast(file: Path, tokens: Stream[Token], types: Types) -> AST:
    ast_generator: AstGenerator = AstGenerator(file, tokens, types).generate()
    ast: AST = ast_generator.ast
    print(*ast.statements.objects, sep="\n")
    return ast


def check_ast(ast: AST) -> None:
    """run several checks on the generated AST"""
    AstCheck(ast).run()


def create_build_folders() -> tuple[Path, Path]:
    build_folder: Path = repo_root / "build" / "compyler"
    header_folder: Path = build_folder / "tapl_headers"
    # ensure the build and header folders exists
    build_folder.mkdir(parents=True, exist_ok=True)
    header_folder.mkdir(parents=True, exist_ok=True)
    return build_folder, header_folder


def generate_code(ast: AST, build_folder: Path, header_folder: Path, templates_folder: Path) -> Path:
    # the new visitor pattern code generator
    generator = CBackendCodeGenerator(ast, build_folder, header_folder, templates_folder)
    generator.generate()
    return generator.get_main_file()


def copy_stdlib(header_folder: Path, stdlib_folder: Path) -> None:
    # recursively copy all header files to the header folder
    # using the neat Path.copy_into function, available since python 3.14
    for header in stdlib_folder.glob("*.h"):
        header.copy_into(header_folder)


def format_files(folder: Path) -> None:
    # recursively find all .c and .h files in the build folder and format all found files
    for file_path in folder.rglob("*.[ch]"):
        if file_path.is_file():
            command: list[str] = ["clang-format", "-i", "--fallback-style=none", str(file_path)]
            returncode: int = execute_command(command).returncode
            if returncode != 0:
                handle_error(f"clang-format failed to format {file_path} with error code {returncode}")


def compile_c(c_file: Path, build_folder: Path) -> Path:
    executable: Path = c_file.parent / "main"

    # remove the old executable (if it exists)
    command: list[str] = ["rm", "-f", str(executable)]
    execute_command(command)

    # directly call the gcc compiler, passing the build folder as additional include path
    command: list[str] = ["gcc", "-O0", "-g3", f"-I{build_folder}", "-o", str(executable), str(c_file)]
    returncode: int = execute_command(command).returncode
    if returncode != 0:
        handle_error(f"gcc returned error code {returncode}")
    return executable


def run_executable(executable: Path):
    command: list[str] = [str(executable)]
    execute_command(command)


def execute_command(command: list[str]) -> CompletedProcess[bytes]:
    """print and execute a command and return its result"""
    print(" ".join(command))
    try:
        result = run(command)
        return result
    except CalledProcessError as e:
        handle_error(f"command '{' '.join(command)}' failed with error code {e.returncode}")
    except FileNotFoundError:
        handle_error(f"command '{command[0]}' not found")


def handle_error(error_msg: str) -> NoReturn:
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


def main():
    # get the 'file' argument from the argument parser
    file: Path = argument_parser()

    # modularize the main and imported files
    module_map: ModuleMap = modularize(file)

    # get the main module from the map to process further
    tokens: Stream[Token] = module_map.modules["main"].module_files[0].tokens

    # apply the two typing passes to the token stream
    types: Types = typing_passes(file, tokens)

    # generate an AST from the tokens
    ast: AST = generate_ast(file, tokens, types)

    # run several checks on the generated AST
    check_ast(ast)

    # formulate the path to output the c-code, and a subfolder for the headers
    build_folder, header_folder = create_build_folders()

    # generate c-code from the AST and write the source files in the build folder
    c_file: Path = generate_code(ast, build_folder, header_folder, templates_folder)

    # copy the files in the standard library to the header folder
    copy_stdlib(header_folder, stdlib_folder)

    # format the generated c-code files
    format_files(build_folder)

    # run the c compiler to compile the file
    executable: Path = compile_c(c_file, build_folder)

    # run the executable
    run_executable(executable)


if __name__ == "__main__":
    main()
