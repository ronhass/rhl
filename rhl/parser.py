import logging
from typing import Callable, Iterable, NoReturn, TypeVar, cast

from . import tokens, ast, exceptions, types

T = TypeVar("T")


logger = logging.getLogger(__name__)


class Parser:
    def __init__(self, _tokens: list[tokens.Token]):
        self.tokens = _tokens
        self.root: ast.Program

        self._cur_index = 0

    def parse(self):
        logger.debug("Start parsing.")
        self.root = self.program()
        logger.debug("End parsing.")

    def _peek_at(self, offset: int) -> tokens.Token | None:
        index = self._cur_index + offset
        return self.tokens[index] if index < len(self.tokens) else None

    def _peek(self) -> tokens.Token | None:
        return self._peek_at(0)

    def _peek_next(self) -> tokens.Token | None:
        return self._peek_at(1)

    def _match(self, class_or_tuple) -> bool:
        return isinstance(self._peek(), class_or_tuple)

    def _match_next(self, class_or_tuple) -> bool:
        return isinstance(self._peek_next(), class_or_tuple)

    def _consume(self, token_types: Iterable[type[tokens.TokenType]] | type[tokens.TokenType]) -> tokens.TokenType | None:
        current = self._peek()
        if current is None:
            return None

        if isinstance(token_types, type):
            token_types = [token_types]
        for token_type in token_types:
            if isinstance(current, token_type):
                self._cur_index += 1
                return current

    def _raise_syntax_error(self, message: str) -> NoReturn:
        line = 0
        column = 0
        if token := self._peek():
            line = token.line + 1
            column = token.column

        raise exceptions.RHLSyntaxError(message=message, lineno=line, column=column)

    def _raise_expected_semicolon(self) -> None:
        self._raise_syntax_error("expected ';' at the end of a statement")

    def _consume_list(self, parse_func: Callable[[], T], open_token: type[tokens.Token] = tokens.LParenToken) -> list[T]:
        if open_token == tokens.LParenToken:
            close_token = tokens.RParenToken
        elif open_token == tokens.LSquareParenToken:
            close_token = tokens.RSquareParentToken
        else:
            raise Exception("invalid open token")

        if not self._consume(open_token):
            self._raise_syntax_error("Expected opening parenthesis")

        res = []
        if not self._match(close_token):
            while True:
                res.append(parse_func())
                if not self._consume(tokens.CommaToken):
                    break

        if not self._consume(close_token):
            self._raise_syntax_error("Expected closing parenthesis")

        return res

    def program(self) -> ast.Program:
        statements = []
        while not self._consume(tokens.EOFToken):
            statements.append(self.declaration())
        return ast.Program(statements=statements)

    def declaration(self) -> ast.Statement:
        if self._match(tokens.IdentifierToken) and self._match_next(tokens.ColonToken):
            return self.var_declaration()
        if self._match(tokens.FunctionToken):
            return self.fun_declaration()
        return self.statement()

    def var_declaration(self) -> ast.Statement:
        if not (identifier := self._consume(tokens.IdentifierToken)):
            raise Exception("Already validated this?!")

        if not self._consume(tokens.ColonToken):
            raise Exception("Already validated this?!")

        _type = None if self._match(tokens.EqualToken) else self._parse_type()

        if not self._consume(tokens.EqualToken):
            self._raise_syntax_error("expected '=' in variable declaration")

        value = self.expression()
        if not self._consume(tokens.SemiColonToken):
            self._raise_expected_semicolon()

        return ast.VarDeclaration(name=identifier, type=_type, expr=value)

    def fun_declaration(self) -> ast.Statement:
        if not self._consume(tokens.FunctionToken):
            raise Exception("Already validated this?!")

        if not (name := self._consume(tokens.IdentifierToken)):
            self._raise_syntax_error("expected function name after 'fun'")

        parameters = self._consume_list(self.fun_argument)

        if not self._consume(tokens.MinusToken) or not self._consume(tokens.GreaterToken):
            self._raise_syntax_error("expected -> after arguments")

        return_type = self._parse_type()

        body = self.block()

        return ast.FunDeclaration(
            name=name,
            parameters=parameters,
            return_type=return_type,
            body=body
        )

    def fun_argument(self) -> tuple[tokens.IdentifierToken, types.Type]:
        if not (name := self._consume(tokens.IdentifierToken)):
            self._raise_syntax_error("expected variable name")

        if not self._consume(tokens.ColonToken):
            self._raise_syntax_error("expected ':' after variable name")

        return (name, self._parse_type())

    def _parse_type(self) -> types.Type:
        if self._consume(tokens.NoneToken):
            return types.none_type

        if identifier := self._consume(tokens.IdentifierToken):
            if identifier.name == "func":
                return self._parse_function_type()

            if identifier.name not in types.basic_types_names:
                self._raise_syntax_error(f"invalid type name {identifier.name}")

            return types.basic_types_names[identifier.name]

        self._raise_syntax_error("invalid type")

    def _parse_function_type(self) -> types.FunctionType:
        if not self._consume(tokens.LSquareParenToken):
            self._raise_syntax_error("invalid function type")

        params_types = self._consume_list(self._parse_type, open_token=tokens.LSquareParenToken)

        if not self._consume(tokens.CommaToken):
            self._raise_syntax_error("invalid function type")

        return_type = self._parse_type()

        if not self._consume(tokens.RSquareParentToken):
            self._raise_syntax_error("invalid function type")

        return types.FunctionType.get_or_create(params_types, return_type)

    def statement(self) -> ast.Statement:
        if self._match(tokens.LBraceToken):
            return self.block()

        if self._match(tokens.IfToken):
            return self.if_statement()

        if self._match(tokens.WhileToken):
            return self.while_statement()

        if self._match(tokens.ReturnToken):
            return self.return_statement()

        expr = self.expression()
        if not self._consume(tokens.SemiColonToken):
            self._raise_expected_semicolon()
        return ast.ExpressionStatement(expr=expr)

    def block(self) -> ast.Block:
        if not self._consume(tokens.LBraceToken):
            self._raise_syntax_error("expected a block beginning")

        statements = []
        while not self._match((tokens.RBraceToken, tokens.EOFToken)):
            statements.append(self.declaration())

        if not self._consume(tokens.RBraceToken):
            raise Exception()

        return ast.Block(statements=statements)

    def if_statement(self) -> ast.Statement:
        if not self._consume(tokens.IfToken):
            raise Exception("Already validated this?!")

        condition = self.expression()
        body = self.statement()
        
        else_body = None
        if self._consume(tokens.ElseToken):
            else_body = self.statement()

        return ast.IfStatement(condition=condition, body=body, else_body=else_body)

    def while_statement(self) -> ast.Statement:
        if not self._consume(tokens.WhileToken):
            raise Exception("Already validated this?!")

        condition = self.expression()
        body = self.statement()
        return ast.WhileStatement(condition=condition, body=body)

    def return_statement(self) -> ast.Statement:
        if not self._consume(tokens.ReturnToken):
            raise Exception("Already validated this?!")

        expr = self.expression()
        if not self._consume(tokens.SemiColonToken):
            self._raise_expected_semicolon()

        return ast.ReturnStatement(expr=expr)

    def expression(self) -> ast.Expression:
        if self._match(tokens.IdentifierToken) and self._match_next(tokens.EqualToken):
            return self.variable_assignment()
        return self.logic()

    def variable_assignment(self) -> ast.Expression:
        if not (identifier := self._consume(tokens.IdentifierToken)):
            raise Exception("Already validated this?!")

        if not self._consume(tokens.EqualToken):
            raise Exception("Already validated this?!")

        value = self.expression()
        return ast.VariableAssignment(name=identifier, expr=value)

    def logic(self) -> ast.Expression:
        return self._binary_expression((tokens.OrToken, tokens.AndToken), self.equality)

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
        while op := self._consume(ops_types):
            expr = ast.BinaryExpression(left=expr, operator=op, right=next_rule())
        return expr

    def unary(self) -> ast.Expression:
        if op := self._consume((tokens.BangToken, tokens.MinusToken)):
            return ast.UnaryExpression(operator=op, right=self.unary())
        return self.call()

    def call(self) -> ast.Expression:
        expr = self.primary()

        while self._match(tokens.LParenToken):
            arguments = self._consume_list(self.expression)
            expr = ast.FunctionCall(expr=expr, arguments=arguments)

        return expr

    def primary(self) -> ast.Expression:
        if token := self._consume(tokens.IntegerToken):
            token = cast(tokens.IntegerToken, token)
            return ast.IntLiteralExpression(value=token.value)

        if token := self._consume(tokens.RationalToken):
            token = cast(tokens.RationalToken, token)
            return ast.RationalLiteralExpression(value=token.value)

        if token := self._consume(tokens.StringToken):
            token = cast(tokens.StringToken, token)
            return ast.StringLiteralExpression(value=token.value)

        if token := self._consume((tokens.TrueToken, tokens.FalseToken)):
            return ast.BooleanLiteralExpression(value=isinstance(token, tokens.TrueToken))

        if token := self._consume(tokens.NoneToken):
            return ast.NoneLiteralExpression()

        if token := self._consume(tokens.IdentifierToken):
            return ast.VariableExpression(identifier=token)

        if self._consume(tokens.LParenToken):
            expr = self.expression()
            if not self._consume(tokens.RParenToken):
                self._raise_syntax_error("expected a closing paranthesis")
            return ast.GroupExpression(expr=expr)

        self._raise_syntax_error("invalid character")
