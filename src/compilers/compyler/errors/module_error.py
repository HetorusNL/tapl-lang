#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path

from .tapl_error import TaplError
from ..utils.colors import Colors
from ..utils.source_location import SourceLocation
from ..utils.utils import Utils


class ModuleError(TaplError):
    def __init__(self, message: str, filename: Path, source_location: SourceLocation | None):
        # extract the source code line and line number from the file
        line: int = Utils.get_source_line_number(filename, source_location)
        source_line: str = Utils.get_source_line(filename, line)

        # construct the separate sections of the error message
        newline: str = f"{Colors.RESET}\n"
        file_path: str = f"{Colors.BOLD}{filename}:{line}:{Colors.RESET}"
        error: str = f"{Colors.BOLD}{Colors.RED}error:{Colors.RESET}"

        # construct the error message itself
        error_str: str = f"{newline}{file_path} {error} {message}\n"
        error_str += f"{line:>4d} | {source_line}"

        # pass it to the base class
        super().__init__(error_str)
