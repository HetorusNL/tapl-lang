#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from enum import Enum


class TokenType(Enum):
    # single character tokens
    BRACE_CLOSE = "}"
    BRACE_OPEN = "{"
    BRACKET_CLOSE = "]"
    BRACKET_OPEN = "["
    COLON = ":"
    COMMA = ","
    DOT = "."
    PAREN_CLOSE = ")"
    PAREN_OPEN = "("
    SEMICOLON = ";"
    TILDE = "~"

    # single or double character tokens
    EQUAL = "="
    EQUAL_EQUAL = "=="
    GREATER = ">"
    GREATER_EQUAL = ">="
    LESS = "<"
    LESS_EQUAL = "<="
    MINUS = "-"
    MINUS_EQUAL = "-="
    NOT = "!"
    NOT_EQUAL = "!="
    PLUS = "+"
    PLUS_EQUAL = "+="
    SLASH = "/"
    SLASH_EQUAL = "/="
    STAR = "*"
    STAR_EQUAL = "*="
    INCREMENT = "++"
    DECREMENT = "--"
    AND = "&"
    AND_AND = "&&"
    OR = "|"
    OR_OR = "||"

    # literals
    IDENTIFIER = "<IDENTIFIER>"
    TYPE = "<TYPE>"
    CHARACTER = "<CHARACTER>"
    NUMBER = "<NUMBER>"
    INLINE_COMMENT = "<INLINE_COMMENT>"
    BLOCK_COMMENT = "<BLOCK_COMMENT>"

    # string-related tokens
    STRING_START = "<STRING_START>"
    STRING_CHARS = "<STRING_CHARS>"
    STRING_EXPR_START = "<STRING_EXPR_START>"
    STRING_EXPR_END = "<STRING_EXPR_END>"
    STRING_END = "<STRING_END"

    # keywords
    BREAK = "break"
    BREAKALL = "breakall"
    CLASS = "class"
    CONTINUE = "continue"
    ELSE = "else"
    FALSE = "false"
    FOR = "for"
    IF = "if"
    IMPORT = "import"
    LIST = "list"
    MODULE = "module"
    NULL = "null"
    PRINT = "print"
    PRINTLN = "println"
    RETURN = "return"
    SUPER = "super"
    THIS = "this"
    TRUE = "true"
    WHILE = "while"

    # special tokens
    INDENT = "<INDENT>"
    DEDENT = "<DEDENT"
    ERROR = "<ERROR>"
    NEWLINE = "<NEWLINE>"

    # end of file/input token
    EOF = "<EOF>"
