from dataclasses import dataclass
from typing import Any

from . import tokens, types


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
class Program(Statement):
    statements: list[Statement]


@dataclass
class VarDeclaration(Statement):
    name: tokens.IdentifierToken
    type: types.Type | None
    expr: Expression


@dataclass
class FunDeclaration(Statement):
    name: tokens.IdentifierToken
    parameters: list[tuple[tokens.IdentifierToken, types.Type]]
    return_type: types.Type
    body: "Block"


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
class ReturnStatement(Statement):
    expr: Expression


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
    scope_distance: int = -1


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
    scope_distance: int = -1


@dataclass
class FunctionCall(Expression):
    expr: Expression
    arguments: list[Expression]
    scope_distance: int = -1
