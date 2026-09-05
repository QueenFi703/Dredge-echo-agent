"""
Parser for Aster (.co files).

Consumes a token stream produced by :mod:`tokenizer` and builds an AST
using the node definitions from :mod:`ast_builder`.

Grammar (from syntax.ebnf):

    program     → statement*
    statement   → entity_decl | action_decl | cycle_decl | action_call
    entity_decl → "entity" IDENTIFIER
    action_decl → "action" IDENTIFIER "(" relation ")"
    relation    → IDENTIFIER "->" IDENTIFIER
    cycle_decl  → "cycle" IDENTIFIER "{" statement* "}"
    action_call → IDENTIFIER
"""

from __future__ import annotations

from typing import List

from .ast_builder import (
    ActionCall,
    ActionDecl,
    CycleDecl,
    EntityDecl,
    Identifier,
    Node,
    Program,
    Relation,
)
from .tokenizer import Token, TokenType


class ParseError(Exception):
    """Raised when the parser encounters a syntax error."""


class Parser:
    """
    Recursive-descent parser for Aster.

    Usage::

        from language.parser.tokenizer import Tokenizer
        from language.parser.parser import Parser

        tokens = Tokenizer(source).tokenize()
        program = Parser(tokens).parse()
    """

    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def parse(self) -> Program:
        """Parse the token stream and return a :class:`Program` AST node."""
        statements: List[Node] = []
        while not self._at_end():
            stmt = self._statement()
            if stmt is not None:
                statements.append(stmt)
        return Program(statements=statements)

    # ------------------------------------------------------------------
    # Grammar rules
    # ------------------------------------------------------------------

    def _statement(self) -> Node | None:
        tok = self._peek()

        if tok.type == TokenType.ENTITY:
            return self._entity_decl()
        if tok.type == TokenType.ACTION:
            return self._action_decl()
        if tok.type == TokenType.CYCLE:
            return self._cycle_decl()
        if tok.type == TokenType.IDENTIFIER:
            return self._action_call()

        # Skip EOF silently; anything else is an error.
        if tok.type == TokenType.EOF:
            return None

        raise ParseError(
            f"Unexpected token {tok.value!r} ({tok.type.name}) "
            f"at line {tok.line}, column {tok.column}"
        )

    def _entity_decl(self) -> EntityDecl:
        kw = self._consume(TokenType.ENTITY)
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected entity name")
        return EntityDecl(name=name_tok.value, line=kw.line, column=kw.column)

    def _action_decl(self) -> ActionDecl:
        kw = self._consume(TokenType.ACTION)
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected action name")
        self._consume(TokenType.LPAREN, "Expected '(' after action name")
        relation = self._relation()
        self._consume(TokenType.RPAREN, "Expected ')' after relation")
        return ActionDecl(
            name=name_tok.value,
            relation=relation,
            line=kw.line,
            column=kw.column,
        )

    def _relation(self) -> Relation:
        src_tok = self._consume(TokenType.IDENTIFIER, "Expected source identifier")
        arrow = self._consume(TokenType.ARROW, "Expected '->' in relation")
        tgt_tok = self._consume(TokenType.IDENTIFIER, "Expected target identifier")
        return Relation(
            source=src_tok.value,
            target=tgt_tok.value,
            line=src_tok.line,
            column=src_tok.column,
        )

    def _cycle_decl(self) -> CycleDecl:
        kw = self._consume(TokenType.CYCLE)
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected cycle name")
        self._consume(TokenType.LBRACE, "Expected '{' after cycle name")

        body: List[Node] = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            stmt = self._statement()
            if stmt is not None:
                body.append(stmt)

        self._consume(TokenType.RBRACE, "Expected '}' to close cycle body")
        return CycleDecl(
            name=name_tok.value,
            body=body,
            line=kw.line,
            column=kw.column,
        )

    def _action_call(self) -> ActionCall:
        tok = self._consume(TokenType.IDENTIFIER)
        return ActionCall(name=tok.value, line=tok.line, column=tok.column)

    # ------------------------------------------------------------------
    # Token stream helpers
    # ------------------------------------------------------------------

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _check(self, ttype: TokenType) -> bool:
        return self._peek().type == ttype

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        if tok.type != TokenType.EOF:
            self._pos += 1
        return tok

    def _consume(self, ttype: TokenType, message: str = "") -> Token:
        if self._check(ttype):
            return self._advance()
        tok = self._peek()
        msg = message or f"Expected {ttype.name}"
        raise ParseError(
            f"{msg}, got {tok.value!r} ({tok.type.name}) "
            f"at line {tok.line}, column {tok.column}"
        )
