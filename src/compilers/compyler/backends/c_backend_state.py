#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.


class CBackendState:
    def __init__(self):
        # create strings for the main source code and function declarations and definitions
        self.main_lines: list[str] = []
        self.function_declarations: list[str] = []
        self.function_definitions: list[str] = []

        # class specific state for the class objects and method declarations and definitions
        self.in_class: bool = False
        self.class_objects: list[str] = []
        self.class_method_declarations: list[str] = []
        self.class_method_definitions: list[str] = []
