#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path

from .c_backend_expression_visitor import CBackendExpressionVisitor
from .c_backend_state import CBackendState
from .c_backend_statement_visitor import CBackendStatementVisitor
from ..types.types import Types
from ..utils.ast import AST


class CBackendCodeGenerator:
    def __init__(self, ast: AST, build_folder: Path, header_folder: Path, templates_folder: Path):
        # store the passed objects in the class
        self._ast: AST = ast
        self._types: Types = ast.types
        self._build_folder: Path = build_folder
        self._header_folder: Path = header_folder
        self._templates_folder: Path = templates_folder

        # create the state and the visitors for the C backend
        self._state = CBackendState()
        self._expression_visitor = CBackendExpressionVisitor(self._state)
        self._statement_visitor = CBackendStatementVisitor(self._state, self._expression_visitor)

    def get_main_file(self) -> Path:
        return self._build_folder / "main.c"

    def generate(self) -> None:
        # generate the utility functions
        self._write_utility_functions()

        # also generate the typedefs for all builtin basic types
        self._write_basic_type_header()
        self._write_list_type_header()

        # loop through the statements in the AST and generate code for each of them
        # the visitors store the generated code in the state
        for statement in self._ast.statements.iter():
            if line := statement.accept(self._statement_visitor):
                self._state.main_lines.append(line)

        # write the classes to the classes c file
        self._write_classes(self._state.class_definitions)

        # write the functions to the functions c file
        self._write_functions(self._state.function_declarations, self._state.function_definitions)

        # write the main c file with the code
        self._write_main_file(self._state.main_lines, self.get_main_file())

    def _write_utility_functions(self) -> None:
        utility_functions_file: Path = self._header_folder / "utility_functions.h"

        lines: list[str] = [
            "#pragma once\n",
            "\n",
            "// include the needed system headers\n",
            "#include <stdio.h>\n",
            "#include <stdlib.h>\n",
            "\n",
            '#define RED "\\x1b[31m"\n',
            '#define GRN "\\x1b[32m"\n',
            '#define YEL "\\x1b[33m"\n',
            '#define BLU "\\x1b[34m"\n',
            '#define MAG "\\x1b[35m"\n',
            '#define CYN "\\x1b[36m"\n',
            '#define WHT "\\x1b[37m"\n',
            '#define RESET "\\x1b[0m"\n',
            "\n",
            "void panic(const char* message) {\n",
            '    fprintf(stderr, RED "panic: %s!\\n" RESET, message);\n',
            "    exit(1);\n",
            "}\n",
        ]

        with open(utility_functions_file, "w") as f:
            f.writelines(lines)

    def _write_basic_type_header(self) -> None:
        # add the strings to be added to the types header
        lines: list[str] = [
            "#pragma once\n",
            "\n",
            "#include <stdbool.h>\n",
            "#include <stdint.h>\n",
            "\n",
            "// typedefs for the builtin basic types defined in TAPL\n",
        ]

        # formulate the typedefs for the basic types used in TAPL
        for type_ in self._types.simple_types.values():
            if type_.is_basic_type:
                # only add the type if it has a different name in c
                if type_.underlying_type != type_.keyword:
                    lines.append(f"typedef {type_.underlying_type} {type_.keyword};\n")

        # write the content to the file
        types_header: Path = self._header_folder / "types.h"
        with open(types_header, "w") as f:
            f.writelines(lines)

    def _write_list_type_header(self) -> None:
        # add the strings to be added to the types header
        lines: list[str] = [
            "#pragma once\n",
            "\n",
            "// include the needed system headers\n",
            "#include <stdio.h>\n",
            "#include <stdlib.h>\n",
            "\n",
            "// also include the needed TAPL headers\n",
            "#include <tapl_headers/types.h>\n",
            "#include <tapl_headers/utility_functions.h>\n",
            "\n",
        ]

        # for every list type, add the filled in template to the source lines
        for type_ in self._types.list_types.values():
            # read the lines from the template
            with open(self._templates_folder / "list.h") as f:
                template_lines: list[str] = f.readlines()
            # replace the "TYPE" text with the actual internal type of the ListType
            list_type: str = type_.inner_type.keyword
            template_lines = [line.replace("TYPE", list_type) for line in template_lines]
            lines.extend(template_lines)

        # write the content to the file
        list_header: Path = self._header_folder / "list.h"
        with open(list_header, "w") as f:
            f.writelines(lines)

    def _write_classes(self, definitions: list[str]) -> None:
        classes_file: Path = self._header_folder / "classes.h"

        initial_lines: list[str] = [
            "#pragma once\n",
            "\n",
            "// include the needed system headers\n",
            "#include <stdio.h>\n",
            "\n",
            "// also include the needed TAPL headers\n",
            "#include <tapl_headers/types.h>\n",
            "\n",
            "// classes declarations\n",
        ]

        with open(classes_file, "w") as f:
            f.writelines(initial_lines)
            f.writelines(definitions)

    def _write_functions(self, declarations: list[str], definitions: list[str]) -> None:
        functions_file: Path = self._header_folder / "functions.h"

        initial_lines: list[str] = [
            "#pragma once\n",
            "\n",
            "// include the needed system headers\n",
            "#include <stdio.h>\n",
            "\n",
            "// also include the needed TAPL headers\n",
            "#include <tapl_headers/types.h>\n",
            "\n",
            "// function declarations\n",
        ]
        definition_lines: list[str] = [
            "\n",
            "// function definitions\n",
        ]

        with open(functions_file, "w") as f:
            f.writelines(initial_lines)
            f.writelines(declarations)
            f.writelines(definition_lines)
            f.writelines(definitions)

    def _write_main_file(self, code_lines: list[str], c_file: Path) -> None:
        initial_lines: list[str] = [
            "// include the needed system headers\n",
            "#include <stdio.h>\n",
            "\n",
            "// also include the needed TAPL headers\n",
            "#include <tapl_headers/classes.h>\n",
            "#include <tapl_headers/file.h>\n",
            "#include <tapl_headers/functions.h>\n",
            "#include <tapl_headers/list.h>\n",
            "#include <tapl_headers/types.h>\n",
            "\n",
            "int main(int argc, char** argv) {\n",
        ]

        with open(c_file, "w") as f:
            f.writelines(initial_lines)
            f.writelines(code_lines)
            f.write("}\n")
