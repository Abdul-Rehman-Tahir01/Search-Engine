"""Boolean query tokenizer and recursive-descent parser.

Grammar (case-insensitive operators):

    Expr    := Term ( OR Term )*
    Term    := Factor ( AND Factor )*
    Factor  := NOT Factor | Primary
    Primary := WORD | LPAREN Expr RPAREN

Operator precedence: NOT > AND > OR
Associativity: left for AND/OR.

This module only parses into an AST; evaluation is performed by
search_engine.boolean_search().
"""

from typing import List, Optional


class Token:
    def __init__(self, kind: str, value: str):
        self.kind = kind  # 'WORD', 'AND', 'OR', 'NOT', 'LPAREN', 'RPAREN'
        self.value = value

    def __repr__(self) -> str:
        return f"Token({self.kind}, {self.value})"


def tokenize(query: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    n = len(query)
    while i < n:
        ch = query[i]
        if ch.isspace():
            i += 1
            continue
        if ch == '(':
            tokens.append(Token('LPAREN', '('))
            i += 1
            continue
        if ch == ')':
            tokens.append(Token('RPAREN', ')'))
            i += 1
            continue

        # quoted phrase treated as a WORD token (single unit)
        if ch in ('"', "'"):
            quote = ch
            j = i + 1
            buf = []
            while j < n and query[j] != quote:
                buf.append(query[j])
                j += 1
            tokens.append(Token('WORD', ''.join(buf)))
            i = j + 1 if j < n else j
            continue

        # read an alphanumeric token
        j = i
        while j < n and (query[j].isalnum() or query[j] in ['_', '-', '.']):
            j += 1
        lex = query[i:j]
        upper = lex.upper()
        if upper == 'AND':
            tokens.append(Token('AND', 'AND'))
        elif upper == 'OR':
            tokens.append(Token('OR', 'OR'))
        elif upper == 'NOT':
            tokens.append(Token('NOT', 'NOT'))
        else:
            tokens.append(Token('WORD', lex))
        i = j

    return tokens


# AST Nodes
class Node:
    pass


class Word(Node):
    def __init__(self, term: str):
        self.term = term

    def __repr__(self) -> str:
        return f"Word({self.term})"


class Not(Node):
    def __init__(self, child: Node):
        self.child = child

    def __repr__(self) -> str:
        return f"Not({self.child})"


class And(Node):
    def __init__(self, parts: List[Node]):
        self.parts = parts

    def __repr__(self) -> str:
        return f"And({self.parts})"


class Or(Node):
    def __init__(self, parts: List[Node]):
        self.parts = parts

    def __repr__(self) -> str:
        return f"Or({self.parts})"


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _consume(self, kind: str) -> Token:
        tok = self._peek()
        if tok is None or tok.kind != kind:
            raise SyntaxError(f"Expected {kind}, got {tok}")
        self.pos += 1
        return tok

    def parse(self) -> Node:
        node = self._parse_expr()
        if self._peek() is not None:
            raise SyntaxError(f"Unexpected token {self._peek()}")
        return node

    def _parse_expr(self) -> Node:
        # Expr := Term ( OR Term )*
        node = self._parse_term()
        parts = [node]
        while True:
            tok = self._peek()
            if tok and tok.kind == 'OR':
                self._consume('OR')
                parts.append(self._parse_term())
            else:
                break
        if len(parts) == 1:
            return parts[0]
        return Or(parts)

    def _parse_term(self) -> Node:
        # Term := Factor ( AND Factor )*
        node = self._parse_factor()
        parts = [node]
        while True:
            tok = self._peek()
            if tok and tok.kind == 'AND':
                self._consume('AND')
                parts.append(self._parse_factor())
            else:
                break
        if len(parts) == 1:
            return parts[0]
        return And(parts)

    def _parse_factor(self) -> Node:
        # Factor := NOT Factor | Primary
        tok = self._peek()
        if tok and tok.kind == 'NOT':
            self._consume('NOT')
            return Not(self._parse_factor())
        return self._parse_primary()

    def _parse_primary(self) -> Node:
        tok = self._peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")
        if tok.kind == 'WORD':
            self._consume('WORD')
            return Word(tok.value)
        if tok.kind == 'LPAREN':
            self._consume('LPAREN')
            node = self._parse_expr()
            self._consume('RPAREN')
            return node
        raise SyntaxError(f"Unexpected token {tok}")


def parse(query: str) -> Node:
    """Tokenize and parse a query string into an AST."""
    return Parser(tokenize(query)).parse()
