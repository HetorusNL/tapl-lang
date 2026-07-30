// Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
//
// This file is part of compyler, a TAPL compiler.

#pragma once

// include the needed system headers
#include <stdint.h>
#include <stdio.h>

// also include the needed TAPL headers
#include <tapl_headers/list.h>

static const size_t BLOCK_SIZE = 256;

bool read_file(const char* filename, list_char* list) {
    // try to open the file specified, return false if not openable
    FILE* file = fopen(filename, "r");
    if (file == NULL)
        return false;

    // the buffer used to read from the file
    u8 buffer[BLOCK_SIZE];

    // continuously read blocks of up to BLOCK_SIZE chars long
    size_t count = 0;
    while (count = fread(buffer, sizeof(buffer[0]), sizeof(buffer) / sizeof(buffer[0]), file)) {
        // add all read characters to the lsit
        for (size_t i = 0; i < count; i++) {
            list_char_add(list, buffer[i]);
        }
    }

    // read finished, and the list is updated in place, return true
    fclose(file);
    return true;
}

bool write_file(const char* filename, list_char* list) {
    // try to open the file specified, return false if not openable
    FILE* file = fopen(filename, "w");
    if (file == NULL)
        return false;

    // the buffer used to write to the file, to speed up the I/O and kernel calls
    u8 buffer[BLOCK_SIZE];

    // continuously construct and write blocks of up to BLOCK_SIZE chars long
    size_t count = 0;
    size_t block_offset = 0;  // start offset of the current block
    while (count < list_char_size(list)) {
        // calculate the index of the current written char to be used for indexing
        size_t index = count - block_offset;
        buffer[index] = list_char_get(list, count);
        count++;
        // if this index fills the buffer, write it to disk and update the block start offset
        if (index + 1 >= BLOCK_SIZE) {
            fwrite(buffer, sizeof(buffer[0]), sizeof(buffer) / sizeof(buffer[0]), file);
            block_offset = count;
        }
    }
    // check if we have one last block to write
    if (count != block_offset) {
        fwrite(buffer, sizeof(buffer[0]), count - block_offset, file);
    }

    // write finished, return true
    fclose(file);
    return true;
}
