#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.


class VisitorError(BaseException):
    def __init__(self, visitor: object, obj: object):
        visitor_name: str = visitor.__class__.__name__
        obj_name: str = obj.__class__.__name__
        super().__init__(f"Visitor '{visitor_name}' does not implement visit function for '{obj_name}'")
