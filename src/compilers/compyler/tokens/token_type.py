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
    AND = "&"
    AND_AND = "&&"
    DECREMENT = "--"
    EQUAL = "="
    EQUAL_EQUAL = "=="
    GREATER = ">"
    GREATER_EQUAL = ">="
    INCREMENT = "++"
    LESS = "<"
    LESS_EQUAL = "<="
    MINUS = "-"
    MINUS_EQUAL = "-="
    NOT = "!"
    NOT_EQUAL = "!="
    OR = "|"
    OR_OR = "||"
    PLUS = "+"
    PLUS_EQUAL = "+="
    SLASH = "/"
    SLASH_EQUAL = "/="
    STAR = "*"
    STAR_EQUAL = "*="

    # literals
    BLOCK_COMMENT = "<BLOCK_COMMENT>"
    CHARACTER = "<CHARACTER>"
    IDENTIFIER = "<IDENTIFIER>"
    INLINE_COMMENT = "<INLINE_COMMENT>"
    NUMBER = "<NUMBER>"
    TYPE = "<TYPE>"

    # string-related tokens
    STRING_CHARS = "<STRING_CHARS>"
    STRING_END = "<STRING_END>"
    STRING_EXPR_END = "<STRING_EXPR_END>"
    STRING_EXPR_START = "<STRING_EXPR_START>"
    STRING_START = "<STRING_START>"

    # keywords
    BREAK = "break"
    BREAKALL = "breakall"
    CLASS = "class"
    CONTINUE = "continue"
    ELSE = "else"
    ENUM = "enum"
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
    RETURN_IF = "return_if"
    SUPER = "super"
    THIS = "this"
    TRUE = "true"
    WHILE = "while"

    # special tokens
    DEDENT = "<DEDENT>"
    ERROR = "<ERROR>"
    INDENT = "<INDENT>"
    NEWLINE = "<NEWLINE>"

    # end of file/input token
    EOF = "<EOF>"
