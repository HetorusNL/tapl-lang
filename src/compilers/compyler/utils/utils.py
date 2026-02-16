#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path

from .colors import Colors
from ..expressions.expression import Expression
from ..expressions.identifier_expression import IdentifierExpression
from .source_location import SourceLocation
from ..types.character_type import CharacterType
from ..types.numeric_type import NumericType
from ..types.numeric_type_type import NumericTypeType
from ..types.type import Type


class Utils:
    """Utility class with several class methods"""

    @classmethod
    def get_source_line_number(cls, filename: Path, source_location: SourceLocation | None) -> int:
        # initial check if a valid SourceLocation is passed
        if not source_location:
            return -1

        # read the entire file info a string
        with open(filename) as f:
            content: str = f.read()

        # sanity check that the SourceLocation start is within the file
        if source_location.start > len(content):
            return -1

        # return the number of newlines until the SourceLocation start
        location_start: int = source_location.start
        return content[:location_start].count("\n") + 1

    @classmethod
    def get_source_line(cls, filename: Path, line: int):
        no_source: str = f"<no source code line available>"
        # initial check if a valid line is passed
        if line < 0:
            return no_source

        # read the file into lines
        with open(filename) as f:
            lines: list[str] = f.readlines()

        # check if the line number exists in the file, return the correct line or error
        if line <= len(lines):
            return lines[line - 1].removesuffix("\n")
        else:
            error = f"[ internal compiler error! (line {line} not found in source) ]"
            return f"{Colors.BOLD}{Colors.RED}{error}{Colors.RESET} {no_source}"

    @classmethod
    def get_source_text(cls, filename: Path, source_location: SourceLocation) -> str:
        # read the entire file info a string
        with open(filename) as f:
            content: str = f.read()

        # sanity check that the SourceLocation start is within the file
        error: str = f"SourceLocation start {source_location.start} is outside the file {filename}"
        assert source_location.start < len(content), error
        source_location_end: int = source_location.start + source_location.length
        error = f"SourceLocation end {source_location_end} is outside the file {filename}"
        assert source_location_end <= len(content), error

        # return the source text within the SourceLocation
        location_start: int = source_location.start
        return content[location_start:source_location_end]

    @classmethod
    def get_expression_type(cls, expression: Expression) -> Type:
        # checks if the type has an inner type, then return the inner type
        if isinstance(expression, IdentifierExpression):
            if expression.inner_expression:
                return cls.get_expression_type(expression.inner_expression)
        # otherwise return the type of the expression
        return expression.type_

    @classmethod
    def get_type_format_string(cls, expression: Expression) -> str:
        type_: Type = cls.get_expression_type(expression)
        match type_:
            case CharacterType():
                return f"%c"
            case NumericType():
                # depending on the size of the type, add 'l' to the format
                long: str = "l" if type_.num_bits > 32 else ""
                match type_.numeric_type_type:
                    case NumericTypeType.SIGNED:
                        return f"%{long}d"
                    case NumericTypeType.UNSIGNED:
                        return f"%{long}u"
                    case NumericTypeType.FLOATING_POINT:
                        return f"%{long}f"
            case _:
                assert False, f"internal compiler error, {type(type_)} not handled!"
