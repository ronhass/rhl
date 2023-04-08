from dataclasses import dataclass
from typing import Any

from . import tokens


@dataclass
class ASTNode:
    pass


@dataclass
class Statement(ASTNode):
    pass


@dataclass
class Expression(ASTNode):
    pass


@dataclass
class Program(ASTNode):
    statements: list[Statement]


@dataclass
class Decleration(Statement):
    name: tokens.IdentifierToken
    type: tokens.IdentifierToken | None
    expr: Expression


@dataclass
class Block(Statement):
    statements: list[Statement]


@dataclass
class IfStatement(Statement):
    condition: Expression
    body: Statement
    else_body: Statement | None


@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: Statement


@dataclass
class ExpressionStatement(Statement):
    expr: Expression


@dataclass
class LiteralExpression(Expression):
    value: Any


@dataclass
class IntLiteralExpression(LiteralExpression):
    value: int


@dataclass
class RationalLiteralExpression(LiteralExpression):
    value: float


@dataclass
class StringLiteralExpression(LiteralExpression):
    value: str


@dataclass
class BooleanLiteralExpression(LiteralExpression):
    value: bool


@dataclass
class NoneLiteralExpression(LiteralExpression):
    value: Any = None


@dataclass
class VariableExpression(Expression):
    identifier: tokens.IdentifierToken


@dataclass
class GroupExpression(Expression):
    expr: Expression


@dataclass
class UnaryExpression(Expression):
    operator: tokens.Token
    right: Expression


@dataclass
class BinaryExpression(Expression):
    left: Expression
    operator: tokens.Token
    right: Expression


@dataclass
class VariableAssignment(Expression):
    name: tokens.IdentifierToken
    expr: Expression
