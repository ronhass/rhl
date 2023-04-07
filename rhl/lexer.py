from typing import Callable, TypeVar

from . import tokens
from .exceptions import RHLSyntaxError

TokenType = TypeVar("TokenType", bound=tokens.Token)


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: list[tokens.Token] = []

        self._cur_line: str = ""
        self._cur_lineno: int = 0
        self._cur_col: int = 0

    def lex(self):
        self.tokens = []

        for lineno, line in enumerate(self.source.splitlines()):
            self._cur_line = line
            self._cur_lineno = lineno
            self._cur_col = 0

            while token := self._next_token():
                self.tokens.append(token)

        self._cur_lineno += 1
        self._cur_col = 0
        self.tokens.append(self._create_token(tokens.EOFToken))

    def _create_token(self, token_type: type[TokenType], **kwargs) -> TokenType:
        return token_type(
            line=self._cur_lineno,
            column=self._cur_col,
            **kwargs
        )

    def _next_token(self) -> tokens.Token | None:
        self._consume_while(lambda c: c.isspace())
        if not self._peek():
            return

        if self._match("#"):
            return

        if token := self._next_number_token():
            return token

        if token := self._next_string_token():
            return token

        if token := self._next_two_chars_token():
            return token

        if token := self._next_one_char_token():
            return token

        if token := self._next_keyword_token():
            return token

        if token := self._next_identifier_token():
            return token

        self._raise_syntax_error("Invalid character")

    def _next_two_chars_token(self) -> tokens.TwoCharsToken | None:
        for two_chars_token in tokens.TwoCharsToken.__subclasses__():
            if self._match(two_chars_token._CHARS):
                return self._create_token(two_chars_token)

    def _next_one_char_token(self) -> tokens.OneCharToken | None:
        for one_char_token in tokens.OneCharToken.__subclasses__():
            if self._match(one_char_token._CHAR):
                return self._create_token(one_char_token)

    def _next_keyword_token(self) -> tokens.KeywordToken | None:
        for keyword_token in tokens.KeywordToken.__subclasses__():
            word = self._slice_line(size=len(keyword_token._KEY))
            if word == keyword_token._KEY:
                if not (after := self._peek_next(offset=len(word))) or after.isspace():
                    self._consume(len(word))
                    return self._create_token(keyword_token)

    def _next_string_token(self) -> tokens.StringToken | None:
        if not self._match('"'):
            return

        value = self._consume_while(lambda c: c != '"')

        if not self._match('"'):
            self._raise_syntax_error("Expected '\"' to terminate string")
        return self._create_token(tokens.StringToken, value=value)

    def _next_number_token(self) -> tokens.IntegerToken | tokens.RationalToken | None:
        is_rational = False
        integer_part = self._consume_while(lambda c: c.isdigit())
        rational_part = ""

        if self._peek() == ".":
            if not (integer_part or self._peek_next().isdigit()):
                return
            self._consume()
            rational_part = self._consume_while(lambda c: c.isdigit())
            is_rational = True

        if not (integer_part or rational_part):
            return

        if is_rational:
            return self._create_token(tokens.RationalToken, value=float(f"{integer_part}.{rational_part}"))
        return self._create_token(tokens.IntegerToken, value=int(integer_part))

    def _next_identifier_token(self) -> tokens.IdentifierToken | None:
        if not (name := self._consume_while(lambda c: c.isalnum() or c == "_")): 
            return

        return self._create_token(tokens.IdentifierToken, name=name)

    def _consume_while(self, cond: Callable[[str], bool]) -> str:
        res = ""
        while (c := self._peek()) and c and cond(c):
            res += self._consume()
        return res

    def _consume(self, size: int = 1) -> str:
        c = self._slice_line(size=size)
        self._cur_col += len(c)
        return c

    def _slice_line(self, start: int | None = None, size: int = 1) -> str:
        if start is None:
            start = self._cur_col
        end = start + size
        return self._cur_line[start:end]

    def _peek(self) -> str:
        return self._slice_line()

    def _peek_next(self, offset: int = 1) -> str:
        return self._slice_line(start=self._cur_col + offset)

    def _match(self, c: str) -> str:
        if self._slice_line(size=len(c)) == c:
            return self._consume(len(c))
        return ""

    def _raise_syntax_error(self, message: str) -> None:
        raise RHLSyntaxError(message=message, lineno=self._cur_lineno + 1, column=self._cur_col)
