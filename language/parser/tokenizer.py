"""
Tokenizer for Aster (.co files).

Breaks source text into a stream of typed tokens that the parser consumes.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List


class TokenType(Enum):
    # Keywords
    ENTITY = auto()
    ACTION = auto()
    CYCLE = auto()

    # Punctuation
    LPAREN = auto()   # (
    RPAREN = auto()   # )
    LBRACE = auto()   # {
    RBRACE = auto()   # }
    ARROW = auto()    # ->

    # Literals
    IDENTIFIER = auto()

    # Control
    NEWLINE = auto()
    EOF = auto()


KEYWORDS = {
    "entity": TokenType.ENTITY,
    "action": TokenType.ACTION,
    "cycle":  TokenType.CYCLE,
}


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"


class TokenizeError(Exception):
    """Raised when the tokenizer encounters unexpected input."""


class Tokenizer:
    """
    Converts a source string into a list of :class:`Token` objects.

    Usage::

        tokenizer = Tokenizer(source)
        tokens = tokenizer.tokenize()
    """

    def __init__(self, source: str) -> None:
        self._source = source
        self._pos = 0
        self._line = 1
        self._column = 1
        self._tokens: List[Token] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def tokenize(self) -> List[Token]:
        """Return the complete token list for the source string."""
        while not self._at_end():
            self._scan_token()
        self._tokens.append(Token(TokenType.EOF, "", self._line, self._column))
        return self._tokens

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _at_end(self) -> bool:
        return self._pos >= len(self._source)

    def _peek(self, offset: int = 0) -> str:
        idx = self._pos + offset
        if idx >= len(self._source):
            return "\0"
        return self._source[idx]

    def _advance(self) -> str:
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return ch

    def _add_token(self, ttype: TokenType, value: str) -> None:
        self._tokens.append(Token(ttype, value, self._line, self._column))

    def _scan_token(self) -> None:
        ch = self._advance()

        # Skip whitespace (except newlines, which are meaningful as statement separators)
        if ch in (" ", "\t", "\r"):
            return

        if ch == "\n":
            # Newlines are recorded but not emitted as significant tokens;
            # the parser works at the statement level.
            return

        if ch == "#":
            # Comment — consume until end of line
            while not self._at_end() and self._peek() != "\n":
                self._advance()
            return

        if ch == "(":
            self._add_token(TokenType.LPAREN, ch)
        elif ch == ")":
            self._add_token(TokenType.RPAREN, ch)
        elif ch == "{":
            self._add_token(TokenType.LBRACE, ch)
        elif ch == "}":
            self._add_token(TokenType.RBRACE, ch)
        elif ch == "-" and self._peek() == ">":
            self._advance()  # consume '>'
            self._add_token(TokenType.ARROW, "->")
        elif ch.isalpha() or ch == "_":
            self._scan_identifier(ch)
        else:
            raise TokenizeError(
                f"Unexpected character {ch!r} at line {self._line}, column {self._column - 1}"
            )

    def _scan_identifier(self, first_char: str) -> None:
        start_col = self._column - 1
        buf = [first_char]
        while not self._at_end() and (self._peek().isalnum() or self._peek() in ("-", "_")):
            buf.append(self._advance())
        word = "".join(buf)
        ttype = KEYWORDS.get(word, TokenType.IDENTIFIER)
        self._tokens.append(Token(ttype, word, self._line, start_col))
