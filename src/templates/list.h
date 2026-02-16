// Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
//
// This file is part of compyler, a TAPL compiler.

// declare the 'single element' of the list
typedef struct list_TYPE_element_struct list_TYPE_element;
struct list_TYPE_element_struct {
    TYPE value;
    list_TYPE_element* next;
};
// declare the list type itself
typedef struct list_TYPE_struct list_TYPE;
struct list_TYPE_struct {
    // the pointers to the first and last element
    list_TYPE_element* head;
    list_TYPE_element* tail;

    // a cache keeping track of the last accessed index, and the corresponding pointer
    bool cache_valid;
    u64 cache_index;
    list_TYPE_element* cache_element;

    // store the size of the list
    u64 size;
};
void list_TYPE_constructor(list_TYPE* this) {
    // initialize the list pointers
    this->head = NULL;
    this->tail = NULL;
    // initialize the cache as invalid
    this->cache_valid = false;
    this->cache_index = 0;
    this->cache_element = NULL;
    // initialize the list size
    this->size = 0;
}
// TODO: destructor
void list_TYPE_cache_invalidate(list_TYPE* this) {
    // clear the cache valid flag
    this->cache_valid = false;
}
// get the size of a list
u64 list_TYPE_size(list_TYPE* this) {
    // return the size from the struct directly
    return this->size;
}
// add an element to the back of the list
void list_TYPE_add(list_TYPE* this, TYPE value) {
    list_TYPE_cache_invalidate(this);
    // construct the new element
    list_TYPE_element* new_element = malloc(sizeof(list_TYPE_element));
    new_element->value = value;
    new_element->next = NULL;

    // handle the empty list case
    if (this->head == NULL) {
        this->head = new_element;
        this->tail = new_element;
        this->size++;
        return;
    }

    // otherwise add it to the tail, and update the tail pointer
    this->tail->next = new_element;
    this->tail = new_element;
    this->size++;
}
// gets the Xth element from the list, panic when it's not there
TYPE list_TYPE_get(list_TYPE* this, u64 index) {
    // remember the requested index for caching
    u64 requested_index = index;

    list_TYPE_element* element = this->head;

    // check if we can use the cache
    if (this->cache_valid && index >= this->cache_index) {
        // start from the cached element
        element = this->cache_element;
        index -= this->cache_index;
    }

    // traverse to the Xth element (if it exists)
    while (element != NULL && index > 0) {
        element = element->next;
        index--;
    }

    // if the item is not found, or the element is NULL, panic
    if (index > 0 || element == NULL)
        panic("index out of bounds in list_TYPE_get");

    // otherwise we have found the element, update the cache and return the value
    this->cache_valid = true;
    this->cache_index = requested_index;
    this->cache_element = element;

    return element->value;
}
// sets the Xth element in the list to value, panic when it's not there
void list_TYPE_set(list_TYPE* this, u64 index, TYPE value) {
    // remember the requested index for caching
    u64 requested_index = index;

    list_TYPE_element* element = this->head;

    // check if we can use the cache
    if (this->cache_valid && index >= this->cache_index) {
        // start from the cached element
        element = this->cache_element;
        index -= this->cache_index;
    }

    // traverse to the Xth element (if it exists)
    while (element != NULL && index > 0) {
        element = element->next;
        index--;
    }

    // if the item is not found, or the element is NULL, panic
    if (index > 0 || element == NULL)
        panic("index out of bounds in list_TYPE_set");

    // otherwise we have found the element, update the cache and update the value
    this->cache_valid = true;
    this->cache_index = requested_index;
    this->cache_element = element;

    element->value = value;
}
// deletes the Xth element from the list, neatly reconnecting the respective pointer(s), panic when it's not there
void list_TYPE_del(list_TYPE* this, u64 index) {
    list_TYPE_cache_invalidate(this);
    // handle the case when it's the first element
    if (index == 0) {
        // check if it exists
        if (this->head == NULL)
            panic("index out of bounds in list_TYPE_del");

        // otherise delete the element and connect the list to the inner element
        list_TYPE_element* inner = this->head->next;
        free(this->head);
        this->head = inner;
        this->size--;

        // check if we deleted the only element, reset the tail pointer
        if (inner == NULL)
            this->tail = NULL;

        return;
    }
    // traverse to the X-1th element (if it exists)
    list_TYPE_element* element = this->head;
    while (element != NULL && index > 1) {
        element = element->next;
        index--;
    }

    // if the item is not found, or the element is NULL, panic
    if (index > 1 || element == NULL || element->next == NULL)
        panic("index out of bounds in list_TYPE_del");

    // otherwise delete the next element and connect the element's next pointer to the next-next element
    list_TYPE_element* inner = element->next->next;
    free(element->next);
    element->next = inner;

    // check if we deleted the last element, if so, update the tail pointer
    if (inner == NULL)
        this->tail = element;

    this->size--;
}
// inserts a value at the Xth position in the list, neatly connecting the respective pointer(s),
// panic when it's not possible
void list_TYPE_insert(list_TYPE* this, u64 index, TYPE value) {
    list_TYPE_cache_invalidate(this);
    // handle the case when it's the first element
    if (index == 0) {
        // add the element to the list and move the current list value to the next pointer
        list_TYPE_element* new_element = malloc(sizeof(list_TYPE_element));
        new_element->value = value;
        new_element->next = this->head;
        this->head = new_element;
        this->size++;
        return;
    }

    // as we add after the element found, reduce the index by one
    index--;

    // traverse to the Xth element (if it exists)
    list_TYPE_element* element = this->head;
    while (element != NULL && index > 0) {
        element = element->next;
        index--;
    }

    // if the item is not found, or the element is NULL, panic
    if (index > 0 || element == NULL)
        panic("index out of bounds in list_TYPE_insert");

    // add the element at the current element's next pointer, and this next pointer points to that
    list_TYPE_element* new_element = malloc(sizeof(list_TYPE_element));
    new_element->value = value;
    new_element->next = element->next;
    element->next = new_element;

    // check if we inserted at the last location, if so, update the tail pointer
    if (new_element->next == NULL)
        this->tail = new_element;

    this->size++;
}
