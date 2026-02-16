# TAPL

Repository with the compiler/examples/documentation of TAPL (Tim's Awesome Programming Language).
The VSCode extension can be found [here](tools/vscode/tapl-lang/README.md) and language server [TODO]().

## Information

Two compilers are created:

- compyler: the bootstrapping compiler, written in python
- tapl/taplc/compiler: the compiler/REPL written in TAPL, compiled using compyler

The compilers compile '.tim' files into c-code, which in turn is compiled in machine code, and run like any other executable.

Homepage: https://tapl-lang.com

## Dependencies

- uv
- gcc
- clang-format

## Usage

Install the uv environment for the compyler by running:

```bash
uv sync
```

Run the following command to watch the tokenizer and AST generator using the unittests and the example `.tim` files in the test directory, and see the output of the tokenizing and AST generation step:

```bash
uv run ptw
```

Run the following command to compile and run the example with the currently implemented functionality:

```bash
uv run -m src.compilers.compyler examples/current_functionality.tim
```

Run the following command to compile and execute any tim file:

```bash
uv run -m src.compilers.compyler /path/to/file.tim
```

## Needed before AoC

- collections: ~~list~~ / hmap

## 'Issues' found during AoC

the following 'features' were found during AoC solving, and should be fixed

- make char and base/u16-related types be used together
- python IndexError in unterminated string on the last line
- fix type checking after boolean operators (e.g. "(value1 >= value2) && !flag" should end up as "bool && bool" and eventually "bool")
- implement a list of class instances
- same symbols multiple times defined should show the correct error, also with functions and lists
- list.add() should support a function call as 'argument'
- add (fancy) enumeration type (that also has something like a to_string() function)
- parsing in string interpolation function skips everything including and after ':'
- string parsing results in errors when the terminating '"' is within the string interpolation section

## TODO

- add warning for unused variables
- char type should be generated as u8, not char
- add error message to the error token and print that instead of "found 'TokenType.ERROR'!"
- modifiable strings
  - add string class-like thing
  - populate the thing in the ast generator
  - resolve variables during code generation
    - something like below for all vars at once?:
      - sprintf(NULL) for size
      - malloc char array
      - in block scope:
      - sprintf(char array)
- add list tests
- clean up list implementation
- make SourceLocation also able to 'add' a Token/Expression/Statement('s source_location)
- refactor identifier expression from TokenExpression to IdentifierExpression
- allow nested IdentifierExpressions/ThisExpressions
- implement or not allow variable assignment during declaration in class
- fix open TODOs in `tokenizer.py`
  - add 0o / e number parsing
  - make distinction between int and float/double numbers
- fix open TODOs in `ast_generator.py`
  - add classes
  - add standard library / built-in function, to do print(..)
    - this needs imports
- fix open TODOs in `token_expression.py`
  - support pointers?
  - after supporting pointers, refactor 0 to NULL
- fix todos in the typing pass:
  - add fancy error-highlighting/pointing in the source code line(s)
- allow type 'upscaling', e.g. u8 -> u16 -> u32 -> u64, in typing pass
- add language server
  - https://pygls.readthedocs.io/en/latest/servers/getting-started.html
  - example: https://github.com/windelbouwman/sauce-os/tree/main/language-server/slang-lang
- use hypothesis tests: https://hypothesis.readthedocs.io/en/latest/
- rewrite code generation to separate backend module instead of in statement/expression

## Ideas

- add public/private to classes, functions
- make everything private by default (classes, functions, members)
- implicit "python modules' class imports", example:
  - `modules/some_module.tim`: `class SomeModule: // blabla`
  - `file.tim`: `from module import SomeModule`
- REPL
  - use Tom's "hot-reload" functionality to 'inject' REPL lines
  - store persistent variables somewhere
- add `returnif` keyword-like thing:
  - an indented block of statements follow this
  - if a statement returns a non-null value, return this from the surrounding function
  - example below

### Examples

`returnif`:

```
Statement statement():
    // very neatly functions returning if they are non-null
    returnif:
        if_statement()
        for_loop_statement()
        print_statement()
        while_loop_statement()

    // outside of the block use a normal return statement
    Expression e = expression()
    return ExpressionStatement(e)
```

## FAQ

## License

MIT License, Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
