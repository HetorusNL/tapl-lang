#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.


class SourceLocation:
    def __init__(self, start: int, length: int):
        self.start: int = start
        self.length: int = length

    def __eq__(self, other: object) -> bool:
        # it must be the same type of object
        if type(other) != SourceLocation:
            return False

        # of the start and length is the same, it's the same SourceLocation
        return self.start == other.start and self.length == other.length

    def __add__(self, other: SourceLocation) -> SourceLocation:
        """add another SourceLocation, returns a new SourceLocation with the greedy sum of both"""
        # calculate the start and end of the greedy sum of both
        start: int = min(self.start, other.start)
        end: int = max(self.start + self.length, other.start + other.length)
        # calculate the length
        length: int = end - start
        return SourceLocation(start, length)

    def __str__(self) -> str:
        return f"<{self.start}:{self.length}>"
