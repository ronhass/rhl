from typing import Callable, Iterable, cast
from . import tokens, ast


class Parser:
    def __init__(self, _tokens: list[tokens.Token]):
        self.tokens = _tokens
        self.expressions: list[ast.Expression] = []

        self._cur_index = 0

    def parse(self):
        while not self._match(tokens.EOFToken):
            self.expressions.append(self.expression())

    def _peek(self) -> tokens.Token | None:
        return self.tokens[self._cur_index] if self._cur_index < len(self.tokens) else None

    def _consume(self) -> tokens.Token | None:
        if current := self._peek():
            self._cur_index += 1
        return current

    def _match(self, token_types: Iterable[type[tokens.Token]] | type[tokens.Token]) -> tokens.Token | None:
        if isinstance(token_types, type):
            token_types = [token_types]
        for token_type in token_types:
            if isinstance(self._peek(), token_type):
                return self._consume()

    def expression(self) -> ast.Expression:
        return self.equality()

    def equality(self) -> ast.Expression:
        return self._binary_expression((tokens.EqualEqualToken, tokens.BangEqualToken), self.comparison)

    def comparison(self) -> ast.Expression:
        return self._binary_expression((tokens.GreaterToken, tokens.GreaterEqualToken, tokens.LessToken, tokens.LessEqualToken), self.term)

    def term(self) -> ast.Expression:
        return self._binary_expression((tokens.PlusToken, tokens.MinusToken), self.factor)

    def factor(self) -> ast.Expression:
        return self._binary_expression((tokens.StarToken, tokens.SlashToken), self.unary)

    def _binary_expression(self, ops_types: Iterable[type[tokens.Token]], next_rule: Callable) -> ast.Expression:
        expr = next_rule()
        while op := self._match(ops_types):
            expr = ast.BinaryExpression(left=expr, operator=op, right=next_rule())
        return expr

    def unary(self) -> ast.Expression:
        if op := self._match((tokens.BangToken, tokens.MinusToken)):
            return ast.UnaryExpression(operator=op, right=self.unary())
        return self.primary()

    def primary(self) -> ast.Expression:
        if token := self._match(tokens.IntegerToken):
            token = cast(tokens.IntegerToken, token)
            return ast.IntLiteralExpression(value=token.value)

        if token := self._match(tokens.RationalToken):
            token = cast(tokens.RationalToken, token)
            return ast.RationalLiteralExpression(value=token.value)

        if token := self._match(tokens.StringToken):
            token = cast(tokens.StringToken, token)
            return ast.StringLiteralExpression(value=token.value)

        if token := self._match((tokens.TrueToken, tokens.FalseToken)):
            return ast.BooleanLiteralExpression(value=isinstance(token, tokens.TrueToken))

        if token := self._match(tokens.NoneToken):
            return ast.NoneLiteralExpression()

        if self._match(tokens.LParenToken):
            expr = self.expression()
            if not self._match(tokens.RParenToken):
                raise Exception()
            return ast.GroupExpression(expr=expr)

        raise Exception()
