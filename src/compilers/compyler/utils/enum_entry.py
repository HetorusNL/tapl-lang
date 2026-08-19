#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from compyler.expressions.expression import Expression
from compyler.expressions.string_expression import StringExpression
from compyler.tokens.identifier_token import IdentifierToken


class EnumEntry:
    def __init__(self, name: IdentifierToken, string_value: StringExpression, value: Expression):
        self.name: IdentifierToken = name
        self.string_value: StringExpression = string_value
        self.value: Expression = value
