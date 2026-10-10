// Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
//
// This file is part of compyler, a TAPL compiler.

// declare the array type itself, and typedef a pointer to this type
typedef struct array_TYPE_struct array_TYPE;
typedef array_TYPE* ptr_array_TYPE;
struct array_TYPE_struct {
    // store the pointer to the array
    TYPE* array;

    // store the size of the array
    u64 size;
};
void array_TYPE_constructor(array_TYPE* this, u64 size) {
    // initialize the array size
    this->size = size;

    // allocate memory for the array
    this->array = (TYPE*)malloc(sizeof(TYPE) * this->size);
}
// TODO: destructor
// get the size of an array
u64 array_TYPE_size(array_TYPE* this) {
    // return the size from the struct directly
    return this->size;
}
// gets the Xth element from the array, panic when outside the array
TYPE array_TYPE_get(array_TYPE* this, u64 index) {
    if (index >= this->size)
        panic("index out of bounds in array_TYPE_get");

    // otherwise return the element at index index
    return this->array[index];
}
// sets the Xth element in the array to value, panic when outside the array
void array_TYPE_set(array_TYPE* this, u64 index, TYPE value) {
    if (index >= this->size)
        panic("index out of bounds in array_TYPE_set");

    // otherwise set the element at index index
    this->array[index] = value;
}
