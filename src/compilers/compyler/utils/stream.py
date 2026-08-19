#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from collections.abc import Iterator

from compyler.errors.stream_error import StreamError


class Stream[T]:
    """encapsulates a stream of objects.

    objects can be appended to the stream.
    there is an iterator over the objects in the stream.
    the object after the last returned iterator object can be requested.
    objects in the iterator can be replaced with other objects.
    while the iterator is running, objects can be added or replaced.
    """

    def __init__(self):
        self.objects: list[T] = []
        self._index: int = 0

    def add(self, *objs: T) -> Stream[T]:
        """extend the stream with the objects provided"""
        self.objects.extend(objs)
        return self

    def last(self) -> T | None:
        if self.objects:
            return self.objects[-1]
        return None

    def iter(self) -> Iterator[T]:
        """returns an iterator over the stream.

        note that the internal state of the iterators from this function are shared!
        """
        self._index = 0
        while self._index < len(self.objects):
            self._index += 1
            yield self.objects[self._index - 1]

    def iter_next(self, offset: int = 0) -> T:
        """returns the object with offset after the last object returned by the iterator,
        initially the index is set to 0, so the first object is returned.
        raises a StreamError if there is no next object
        """
        position: int = self._index + offset
        if position < len(self.objects):
            return self.objects[position]
        raise StreamError("outside of stream's objects!")

    def replace(self, count: int, replacement: T) -> None:
        """replaces [count] objects with [replacement].
        starting from the element last returned by the call to next
        """
        # negative count values are not possible
        if count < 0:
            raise StreamError("can't replace negative amount of objects!")

        # sanity check the instance's index
        if self._index == 0:
            raise StreamError("invalid state of the iterator!")
        if self._index > len(self.objects) + 1:
            raise StreamError("iterator is outside of stream's objects!")

        # speed up the edge case where count is 1, replace the object
        if count == 1:
            self.objects[self._index - 1] = replacement
            return

        # other cases, delete count objects (when nonzero count)
        if count != 0:
            # check that we can delete count objects
            if self._index + count - 1 > len(self.objects):
                raise StreamError("can't replace this many objects")
            # success, delete the objects
            del self.objects[self._index - 1 : self._index - 1 + count]
        # and add replacement
        self.objects.insert(self._index - 1, replacement)

    def __len__(self) -> int:
        """returns the length of the objects currently in the stream"""
        return len(self.objects)
