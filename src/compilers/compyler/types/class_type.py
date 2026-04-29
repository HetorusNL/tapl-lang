#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from .type import Type


class ClassType(Type):
    def __init__(self, keyword: str):
        # create a simple super class for this class type
        super().__init__(keyword)
