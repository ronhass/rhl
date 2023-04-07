from typing import Callable, Iterable, cast
from . import tokens, ast, exceptions


class Parser:
    def __init__(self, _tokens: list[tokens.Token]):
        self.tokens = _tokens
        self.root: ast.Program

        self._cur_index = 0

    def parse(self):
        self.root = self.program()

    def _peek_at(self, offset: int) -> tokens.Token | None:
        index = self._cur_index + offset
        return self.tokens[index] if index < len(self.tokens) else None

    def _peek(self) -> tokens.Token | None:
        return self._peek_at(0)

    def _peek_next(self) -> tokens.Token | None:
        return self._peek_at(1)

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

    def _raise_syntax_error(self, message: str) -> None:
        line = 0
        column = 0
        if token := self._peek():
            line = token.line + 1
            column = token.column

        raise exceptions.RHLSyntaxError(message=message, lineno=line, column=column)

    def _raise_expected_semicolon(self) -> None:
        self._raise_syntax_error("expected ';' at the end of a statement")

    def program(self) -> ast.Program:
        statements = []
        while not self._match(tokens.EOFToken):
            statements.append(self.decleration())
        return ast.Program(statements=statements)

    def decleration(self) -> ast.Statement:
        if isinstance(self._peek(), tokens.IdentifierToken) and isinstance(self._peek_next(), tokens.ColonToken):
            return self.var_decleration()
        return self.statement()

    def var_decleration(self) -> ast.Statement:
        if not (identifier := self._match(tokens.IdentifierToken)):
            raise Exception("Already validated this?!")

        if not self._match(tokens.ColonToken):
            raise Exception("Already validated this?!")

        type_identifier = self._match(tokens.IdentifierToken)

        if not self._match(tokens.EqualToken):
            self._raise_syntax_error("expected '=' in variable decleration")

        value = self.expression()
        if not self._match(tokens.SemiColonToken):
            self._raise_expected_semicolon()

        return ast.Decleration(name=identifier, type=type_identifier, expr=value)

    def statement(self) -> ast.Statement:
        expr = self.expression()
        if not self._match(tokens.SemiColonToken):
            self._raise_expected_semicolon()
        return ast.ExpressionStatement(expr=expr)

    def expression(self) -> ast.Expression:
        if isinstance(self._peek(), tokens.IdentifierToken) and isinstance(self._peek_next(), tokens.EqualToken):
            return self.variable_assignment()
        return self.equality()

    def variable_assignment(self) -> ast.Expression:
        if not (identifier := self._match(tokens.IdentifierToken)):
            raise Exception("Already validated this?!")

        if not self._match(tokens.EqualToken):
            raise Exception("Already validated this?!")

        value = self.expression()
        return ast.VariableAssignment(name=identifier, expr=value)

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

        if token := self._match(tokens.IdentifierToken):
            return ast.VariableExpression(identifier=token)

        if self._match(tokens.LParenToken):
            expr = self.expression()
            if not self._match(tokens.RParenToken):
                self._raise_syntax_error("expected a closing paranthesis")
            return ast.GroupExpression(expr=expr)

        self._raise_syntax_error("invalid character")
