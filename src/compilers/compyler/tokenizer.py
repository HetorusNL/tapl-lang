#!/usr/bin/env python
#
# Copyright (c) 2026 Tim Klein Nijenhuis <tim@hetorus.nl>
#
# This file is part of compyler, a TAPL compiler.

from pathlib import Path

from .tokens.token_type import TokenType
from .tokens.character_token import CharacterToken
from .tokens.comment_token import CommentToken
from .tokens.identifier_token import IdentifierToken
from .tokens.number_token import NumberToken
from .tokens.string_chars_token import StringCharsToken
from .tokens.token import Token
from .utils.source_location import SourceLocation
from .utils.stream import Stream


class Tokenizer:
    INDENT_SPACES: int = 4

    def __init__(self, file: Path):
        print(f'tokenizing file: "{file}"')
        # for this compiler files will be small enough to load entirely into a string in memory
        with open(file) as f:
            self._file_characters: str = "".join(f.readlines())
        self._file_size: int = len(self._file_characters)

        # some variables to store the state of the tokenizer
        self._current_index: int = 0
        self._line: int = 1
        self._string_var_parsing_depth = 0  # an int as nested strings can happen
        # indent and dedent related variables
        self._at_start_of_line: bool = True
        self._current_indent: int = 0  # current number of INDENT_SPACES indentations
        # the resulting tokens from the tokenizer
        self._tokens: Stream[Token] = Stream()
        # the discarded tokens from the tokenizer (comments, additional newlines, etc)
        self._discarded_tokens: Stream[Token] = Stream()

    def tokenize(self) -> Stream[Token]:
        """tokenize the file and return a token stream"""
        # infinite loop until we reach the end of file
        while True:
            if self._at_start_of_line:
                # if there are any following empty lines, consume them
                self._consume_empty_lines()
                # process indent/dedent from spaces at start of line
                self._add_indent_dedent()

            # switch-case for the next character
            match char := self._next():
                # match all single-character tokens
                case TokenType.BRACE_CLOSE.value:
                    # check if we're in string var parsing mode (at least 1 level deep)
                    if self._string_var_parsing_depth > 0:
                        # add the string var end token
                        self._add_token(TokenType.STRING_EXPR_END)
                        # exit from one level of depth of the string var parsing counter
                        self._string_var_parsing_depth -= 1
                        # continue parsing string chars
                        self._add_string_chars()
                    else:
                        self._add_token_of_length(TokenType.BRACE_CLOSE)
                case TokenType.BRACE_OPEN.value:
                    self._add_token_of_length(TokenType.BRACE_OPEN)
                case TokenType.BRACKET_CLOSE.value:
                    self._add_token_of_length(TokenType.BRACKET_CLOSE)
                case TokenType.BRACKET_OPEN.value:
                    self._add_token_of_length(TokenType.BRACKET_OPEN)
                case TokenType.COLON.value:
                    self._add_token_of_length(TokenType.COLON)
                case TokenType.COMMA.value:
                    self._add_token_of_length(TokenType.COMMA)
                case TokenType.DOT.value:
                    self._add_token_of_length(TokenType.DOT)
                case TokenType.PAREN_CLOSE.value:
                    self._add_token_of_length(TokenType.PAREN_CLOSE)
                case TokenType.PAREN_OPEN.value:
                    self._add_token_of_length(TokenType.PAREN_OPEN)
                case TokenType.SEMICOLON.value:
                    self._add_token_of_length(TokenType.SEMICOLON)
                case TokenType.TILDE.value:
                    self._add_token_of_length(TokenType.TILDE)
                # match all single- or double-character tokens
                case TokenType.EQUAL.value:
                    if self._consume(TokenType.EQUAL.value):
                        self._add_token_of_length(TokenType.EQUAL_EQUAL)
                    else:
                        self._add_token_of_length(TokenType.EQUAL)
                case TokenType.GREATER.value:
                    if self._consume(TokenType.EQUAL.value):
                        self._add_token_of_length(TokenType.GREATER_EQUAL)
                    else:
                        self._add_token_of_length(TokenType.GREATER)
                case TokenType.LESS.value:
                    if self._consume(TokenType.EQUAL.value):
                        self._add_token_of_length(TokenType.LESS_EQUAL)
                    else:
                        self._add_token_of_length(TokenType.LESS)
                case TokenType.MINUS.value:
                    if self._consume(TokenType.MINUS.value):
                        self._add_token_of_length(TokenType.DECREMENT)
                    elif self._consume(TokenType.EQUAL.value):
                        self._add_token_of_length(TokenType.MINUS_EQUAL)
                    else:
                        self._add_token_of_length(TokenType.MINUS)
                case TokenType.NOT.value:
                    if self._consume(TokenType.EQUAL.value):
                        self._add_token_of_length(TokenType.NOT_EQUAL)
                    else:
                        self._add_token_of_length(TokenType.NOT)
                case TokenType.PLUS.value:
                    if self._consume(TokenType.PLUS.value):
                        self._add_token_of_length(TokenType.INCREMENT)
                    elif self._consume(TokenType.EQUAL.value):
                        self._add_token_of_length(TokenType.PLUS_EQUAL)
                    else:
                        self._add_token_of_length(TokenType.PLUS)
                case TokenType.SLASH.value:
                    if self._consume(TokenType.SLASH.value):
                        self._add_inline_comment()
                    elif self._consume(TokenType.STAR.value):
                        self._add_block_comment()
                    elif self._consume(TokenType.EQUAL.value):
                        self._add_token_of_length(TokenType.SLASH_EQUAL)
                    else:
                        self._add_token_of_length(TokenType.SLASH)
                case TokenType.STAR.value:
                    if self._consume(TokenType.EQUAL.value):
                        self._add_token_of_length(TokenType.STAR_EQUAL)
                    else:
                        self._add_token_of_length(TokenType.STAR)
                case TokenType.AND.value:
                    if self._consume(TokenType.AND.value):
                        self._add_token_of_length(TokenType.AND_AND)
                    else:
                        self._add_token_of_length(TokenType.AND)
                case TokenType.OR.value:
                    if self._consume(TokenType.OR.value):
                        self._add_token_of_length(TokenType.OR_OR)
                    else:
                        self._add_token_of_length(TokenType.OR)
                # match special EOF case, we parsed the whole file
                case None:
                    self._add_token(TokenType.EOF)
                    break
                # match characters, numbers and strings
                case "'":
                    self._add_character()
                case digit if self._isdigit(char):
                    # first match a digit, as identifiers can't start with a digit
                    self._add_number(digit)
                case '"':
                    self._start_string()
                case identifier_char if self._is_identifier_char(char):
                    self._add_identifier(identifier_char)
                # match whitespaces
                case " ":
                    pass
                case "\n":
                    self._add_newline(self._current_index - 1)
                case "\r":
                    # why use carriage return..
                    pass
                case "\t":
                    print("error: dammit, we use spaces not tabs!")
                    self._add_token(TokenType.ERROR)
                case _:
                    print(f"unknown character '{char}', skipped...")
                    self._add_token(TokenType.ERROR)
            # after \n we're at start of line, we can expect indent/dedent here
            self._at_start_of_line = char == "\n"
        return self._tokens

    def _next(self) -> str | None:
        """consume and return the next character in the file"""
        return self._get_char(consume=True)

    def _consume(self, char: str) -> bool:
        """check if the next character matches, consumes when matching"""
        # check that the next character matches the one providing
        match: bool = self._get_char(consume=False) == char
        # if it's a match, consume it by incrementing the idex
        if match:
            self._current_index += 1
        # return whether it was a match
        return match

    def _get_char(self, consume: bool, offset: int = 0) -> str | None:
        """utility function to combine _next and _consume"""
        # make sure to check the file size
        if self._current_index + offset >= self._file_size:
            return None
        # otherwise return the next character
        character: str = self._file_characters[self._current_index + offset]
        if consume:
            self._current_index += 1 + offset
        return character

    def _isbinary(self, char: str) -> bool:
        return "0" <= char <= "1"

    def _isdigit(self, char: str) -> bool:
        return "0" <= char <= "9"

    def _ishex(self, char: str) -> bool:
        return self._isdigit(char) or "a" <= char.lower() <= "f"

    def _isalpha(self, char: str) -> bool:
        return "a" <= char <= "z" or "A" <= char <= "Z"

    def _is_identifier_char(self, char: str) -> bool:
        return self._isdigit(char) or self._isalpha(char) or char == "_"

    def _add_character_token(self, value: str, start: int, length: int) -> None:
        source_location: SourceLocation = SourceLocation(start, length)
        character_token: CharacterToken = CharacterToken(source_location, value)
        self._tokens.add(character_token)

    def _add_identifier_token(self, value: str) -> None:
        length: int = len(value)
        start: int = self._current_index - length
        source_location: SourceLocation = SourceLocation(start, length)
        identifier_token: IdentifierToken = IdentifierToken(source_location, value)
        self._tokens.add(identifier_token)

    def _add_number_token(self, value: int, start: int, length: int) -> None:
        source_location: SourceLocation = SourceLocation(start, length)
        number_token: NumberToken = NumberToken(source_location, value)
        self._tokens.add(number_token)

    def _add_string_token(self, value: str) -> None:
        length: int = len(value)
        start: int = self._current_index - length
        source_location: SourceLocation = SourceLocation(start, length)
        string_token: StringCharsToken = StringCharsToken(source_location, value)
        self._tokens.add(string_token)

    def _add_comment_token(self, token_type: TokenType, value: str) -> None:
        length: int = len(value)
        start: int = self._current_index - length
        source_location: SourceLocation = SourceLocation(start, length)
        comment_token: CommentToken = CommentToken(token_type, source_location, value)
        self._discarded_tokens.add(comment_token)

    def _add_token_of_length(self, token_type: TokenType) -> None:
        """Adds a token of length of token_type value consumed characters"""
        length: int = len(token_type.value)
        self._add_token(token_type, self._current_index - length, length)

    def _add_token(self, token_type: TokenType, start: int | None = None, length: int | None = None) -> None:
        """Adds a token at the current (consumed) position with length of 1 (unless different start-length is passed)"""
        start = self._current_index - 1 if start is None else start
        length = 1 if length is None else length
        token: Token = Token(token_type, SourceLocation(start, length))
        self._tokens.add(token)

    def _add_newline(self, start: int) -> None:
        newline_token: Token = Token(TokenType.NEWLINE, SourceLocation(start, 1))
        self._line += 1
        # if the previous token was also a newline, add it to the discarded tokens stream
        last_token: Token | None = self._tokens.last()
        if not last_token or last_token.token_type in [TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT]:
            self._discarded_tokens.add(newline_token)
        else:
            self._tokens.add(newline_token)

    def _add_binary_number(self) -> None:
        """parse a binary number starting with 0b, or an error token if invalid"""
        binary_str: str = "0b"
        self._current_index += 1
        while char := self._get_char(consume=False):
            if self._isbinary(char):
                binary_str += char
                self._current_index += 1
                continue
            break
        length: int = len(binary_str)
        start: int = self._current_index - length
        if length == 2:
            print(f'invalid binary value "{binary_str}"!')
            self._add_token(TokenType.ERROR, start, length)
        else:
            self._add_number_token(int(binary_str, 2), start, length)

    def _add_hexadecimal_number(self) -> None:
        """parse a hexadecimal number starting with 0x, or an error token if invalid"""
        hexadecimal_str: str = "0x"
        self._current_index += 1
        while char := self._get_char(consume=False):
            if self._ishex(char):
                hexadecimal_str += char
                self._current_index += 1
                continue
            break
        length: int = len(hexadecimal_str)
        start: int = self._current_index - length
        if len(hexadecimal_str) == 2:
            print(f'invalid hexadecimal value "{hexadecimal_str}"!')
            self._add_token(TokenType.ERROR, start, length)
        else:
            self._add_number_token(int(hexadecimal_str, 16), start, length)

    def _add_character(self) -> None:
        # the opening quote is already consumed, add the character itself
        character: str | None = self._next()
        if not character:
            print("unterminated character!")
            return self._add_token(TokenType.ERROR, self._current_index - 1, 1)

        if character == "\\":
            # handle escape sequences
            escape_char: str | None = self._next()
            if not escape_char or escape_char not in ["n", "r", "t", "'", "\\"]:  # valid escape sequences
                print(f"unknown escape sequence '{character}{escape_char}'!")
                return self._add_token(TokenType.ERROR, self._current_index - 2, 2)
            character = character + escape_char

        closing_quote: str | None = self._next()
        if closing_quote == "'":
            # we found a character, create the token and return
            return self._add_character_token(character, self._current_index - 3, 3)
        # handle the errors: no character and invalid character
        if not closing_quote:
            print("unterminated character!")
            return self._add_token(TokenType.ERROR, self._current_index - 2, 2)
        print("expected ''' after character")
        return self._add_token(TokenType.ERROR, self._current_index - 3, 3)

    def _add_number(self, first_char: str) -> None:
        # TODO: add distinction between int and float/double
        # TODO: add e numbers, e.g. 1e3, for int and float/double
        # differentiate between binary, hexadecimal, 0-prefixed and normal numbers
        if first_char == "0":
            match char := self._get_char(consume=False):
                case "b":
                    return self._add_binary_number()
                case "x":
                    return self._add_hexadecimal_number()
                case None:
                    # EOF, the file ends with number '0'
                    return self._add_number_token(0, self._current_index - 1, 1)
                case _ if self._isdigit(char):
                    # ordinary number prefixed with a '0', parse below
                    pass
                case _:
                    # the value '0'
                    return self._add_number_token(0, self._current_index - 1, 1)

        number_str: str = first_char
        while char := self._get_char(consume=False):
            # while we get digits, consume them and continue
            if self._isdigit(char):
                number_str += char
                self._current_index += 1
                continue
            break
        length: int = len(number_str)
        start: int = self._current_index - length
        self._add_number_token(int(number_str), start, length)

    def _start_string(self) -> None:
        # store the opening quote
        self._add_token(TokenType.STRING_START)
        # then start consuming the string chars
        self._add_string_chars()

    def _add_string_chars(self) -> None:
        # consume all chars until a closing quote or string var start is encountered
        string: str = ""
        while char := self._get_char(consume=False):
            # wait until we get a closing quote
            if char == '"':
                # first add the string until now
                self._add_string_token(string)
                # then consume and add the closing quote
                self._current_index += 1
                self._add_token(TokenType.STRING_END)
                return
            # if we have a string var start token, add this and continue parsing
            if char == TokenType.BRACE_OPEN.value:
                # first add the string until now
                self._add_string_token(string)
                # consume and add the string var start token
                self._current_index += 1
                self._add_token(TokenType.STRING_EXPR_START)
                # transition to string var parsing mode (one level deeper)
                self._string_var_parsing_depth += 1
                return
            # if we have a newline, then raise an error as the string is unterminated
            if char == "\n":
                length: int = len(string)
                start: int = self._current_index - length
                print(f'unterminated string "{string}"!')
                self._add_token(TokenType.ERROR, start, length)
                return
            # append to the string and consume the character
            string += char
            self._current_index += 1
        # also handle the empty file case
        length: int = len(string)
        start: int = self._current_index - length
        print(f'unterminated string "{string}"!')
        self._add_token(TokenType.ERROR, start, length)
        return

    def _add_keyword(self, identifier: str) -> bool:
        match identifier:
            case TokenType.BREAK.value:
                self._add_token_of_length(TokenType.BREAK)
            case TokenType.BREAKALL.value:
                self._add_token_of_length(TokenType.BREAKALL)
            case TokenType.CLASS.value:
                self._add_token_of_length(TokenType.CLASS)
            case TokenType.CONTINUE.value:
                self._add_token_of_length(TokenType.CONTINUE)
            case TokenType.ELSE.value:
                self._add_token_of_length(TokenType.ELSE)
            case TokenType.FALSE.value:
                self._add_token_of_length(TokenType.FALSE)
            case TokenType.FOR.value:
                self._add_token_of_length(TokenType.FOR)
            case TokenType.IF.value:
                self._add_token_of_length(TokenType.IF)
            case TokenType.IMPORT.value:
                self._add_token_of_length(TokenType.IMPORT)
            case TokenType.LIST.value:
                self._add_token_of_length(TokenType.LIST)
            case TokenType.MODULE.value:
                self._add_token_of_length(TokenType.MODULE)
            case TokenType.NULL.value:
                self._add_token_of_length(TokenType.NULL)
            case TokenType.PRINT.value:
                self._add_token_of_length(TokenType.PRINT)
            case TokenType.PRINTLN.value:
                self._add_token_of_length(TokenType.PRINTLN)
            case TokenType.RETURN.value:
                self._add_token_of_length(TokenType.RETURN)
            case TokenType.SUPER.value:
                self._add_token_of_length(TokenType.SUPER)
            case TokenType.THIS.value:
                self._add_token_of_length(TokenType.THIS)
            case TokenType.TRUE.value:
                self._add_token_of_length(TokenType.TRUE)
            case TokenType.WHILE.value:
                self._add_token_of_length(TokenType.WHILE)
            case _:
                # in de default case we haven't found a keyword
                return False
        # if we matched anything but the default case, we found a keyword
        return True

    def _add_inline_comment(self) -> None:
        comment_text = "//"
        while char := self._next():
            # while we get comment characters, consume them and continue
            if char == "\n":
                # restore the '\n', so the tokenizer can process it
                self._current_index -= 1
                break
            else:
                # add the character to the comment
                comment_text += char
        self._add_comment_token(TokenType.INLINE_COMMENT, comment_text)

    def _add_block_comment(self) -> None:
        comment_text = "/*"
        while char := self._next():
            # if we get an ending "*/", add the block comment token
            if char == "*" and self._consume("/"):
                comment_text += "*/"
                break
            else:
                # add the character to the comment
                comment_text += char
                # increment line number here
                self._line += 1
        else:
            # unterminated block comment
            print(f'unterminated block comment "{comment_text}"!')
            length: int = len(comment_text)
            start: int = self._current_index - length
            self._add_token(TokenType.ERROR, start, length)
            return
        self._add_comment_token(TokenType.BLOCK_COMMENT, comment_text)

    def _add_identifier(self, first_alpha: str) -> None:
        identifier = first_alpha
        while char := self._get_char(consume=False):
            # while we get identifier characters, consume them and continue
            if self._is_identifier_char(char):
                identifier += char
                self._current_index += 1
                continue
            break

        # match keywords, and return if the identifier is a keyword
        if self._add_keyword(identifier):
            return

        # otherwise we have found an identifier
        self._add_identifier_token(identifier)

    def _is_whitespace(self, char: str) -> bool:
        return char in " \n\r\t"

    def _consume_empty_lines(self) -> None:
        # if we have a line with only whitespace characters and a newline, consume it
        offset: int = 0
        while char := self._get_char(False, offset=offset):
            if not self._is_whitespace(char):
                # not whitespace, so not an empty line
                return

            if char == "\n":
                # found a newline, add newline to discarded tokens
                self._add_newline(self._current_index + offset)
                # consume all characters including newline
                self._get_char(True, offset=offset)
                # reset the offset
                offset = 0
                continue

            offset += 1

        # found EOF (char is None), consume all whitespace characters until here
        if offset == 0:
            # special case, no characters before EOF
            return
        # otherwise consume all characters before EOF
        self._get_char(True, offset - 1)

    def _add_indent_dedent(self) -> None:
        spaces: int = 0
        while self._consume(" "):
            spaces += 1

        start: int = self._current_index - spaces

        if spaces % self.INDENT_SPACES != 0:
            print(f"indentations must be a multiple of {self.INDENT_SPACES} spaces!")
            self._add_token(TokenType.ERROR, start, spaces)

        indent: int = spaces // self.INDENT_SPACES
        if indent > self._current_indent:
            # found one or more indentations
            for _ in range(indent - self._current_indent):
                self._add_token(TokenType.INDENT, start, spaces)
        elif indent < self._current_indent:
            # found one or more dedentations
            for _ in range(self._current_indent - indent):
                self._add_token(TokenType.DEDENT, start, spaces)

        # store the current amount of indentations
        self._current_indent: int = indent
