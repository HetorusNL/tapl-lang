#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.errors.tapl_error import TaplError
from compyler.utils.colors import Colors


class StreamError(TaplError):
    def __init__(self, message: str):
        # construct the separate sections of the error message
        newline: str = f"{Colors.RESET}\n"
        error: str = f"{Colors.BOLD}{Colors.RED}internal compiler error:{Colors.RESET}"

        # construct the error message itself
        error_str: str = f"{newline}{error} {message}"

        # pass it to the base class
        super().__init__(error_str)
