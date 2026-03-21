#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.


class CBackendState:
    def __init__(self):
        # create strings for the classes, functions and the main source code lines
        self.class_definitions: list[str] = []
        self.function_declarations: list[str] = []
        self.function_definitions: list[str] = []
        self.main_lines: list[str] = []
