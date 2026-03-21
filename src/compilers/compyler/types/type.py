#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.


class Type:
    _unknown: Type | None = None

    def __init__(self, keyword: str, syntactic_sugar: list[str] = [], underlying_type: str | None = None):
        self.keyword: str = keyword
        self.syntactic_sugar: list[str] = syntactic_sugar
        self.underlying_type: str | None = underlying_type
        self.is_reference: bool = False

    @classmethod
    def unknown(cls):
        """function to get a reference to to a default-unknown Type"""
        # check if the unknown type has been created before, otherwise one
        if cls._unknown is None:
            cls._unknown = Type("unknown")
        # return the created unknown Type
        return cls._unknown

    def reference(self) -> str:
        return f"*" if self.is_reference else f""

    @property
    def all_keywords(self) -> list[str]:
        """returns, in any order, the keyword and syntactic sugars as list"""
        keywords: list[str] = [self.keyword]
        keywords.extend(self.syntactic_sugar)
        return keywords

    @property
    def is_basic_type(self) -> bool:
        """returns whether this is a basic type, that it has an underlying c-type"""
        return self.underlying_type is not None

    def non_void(self) -> bool:
        """returns whether the type is not of type void"""
        return self.keyword != "void"

    @property
    def name(self) -> str:
        """the name of the type, which is its keyword"""
        return self.keyword

    def __eq__(self, other: object) -> bool:
        """two types are equal when they have the same keyword"""
        if not isinstance(other, Type):
            return False

        return self.keyword == other.keyword

    def __str__(self) -> str:
        return f"{self.keyword}"
