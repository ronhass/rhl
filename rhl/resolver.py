import logging
from functools import singledispatchmethod
from . import ast, scope, tokens, types


logger = logging.getLogger(__name__)


class Resolver:
    def __init__(self):
        self._scope = scope.GLOBAL_SCOPE
        self._scope.push()

        self._expected_return_types = []

    @singledispatchmethod
    def resolve_statement(self, stmt: ast.Statement) -> None:
        raise NotImplementedError()

    @resolve_statement.register
    def _(self, stmt: ast.Program) -> None:
        logger.debug("Start resolving.")
        for _stmt in stmt.statements:
            self.resolve_statement(_stmt)
        logger.debug("End resolving.")

    @resolve_statement.register
    def _(self, stmt: ast.VarDeclaration) -> None:
        expression_type = self.resolve_expression(stmt.expr)

        if stmt.type and not stmt.type.can_assign(expression_type):
            raise Exception(f"Cannot assign {expression_type} expression to a {stmt.type} variable")

        self._scope.declare(stmt.name.name, stmt.type or expression_type)

    @resolve_statement.register
    def _(self, stmt: ast.FunDeclaration) -> None:
        logger.debug(f"Entering function '{stmt.name.name}'")
        func_type = types.FunctionType.get_or_create([param_type for _, param_type in stmt.parameters], stmt.return_type)
        self._scope.declare(stmt.name.name, func_type)

        self._scope.push()
        for param_name, param_type in stmt.parameters:
            self._scope.declare(param_name.name, param_type)
        self._expected_return_types.insert(0, stmt.return_type)

        self.resolve_statement(stmt.body)

        self._expected_return_types.pop(0)
        self._scope.pop()

        logger.debug(f"Exiting function '{stmt.name.name}'")

    @resolve_statement.register
    def _(self, stmt: ast.Block) -> None:
        for _stmt in stmt.statements:
            self.resolve_statement(_stmt)

    @resolve_statement.register
    def _(self, stmt: ast.IfStatement) -> None:
        self.resolve_expression(stmt.condition)
        self.resolve_statement(stmt.body)
        if stmt.else_body:
            self.resolve_statement(stmt.else_body)

    @resolve_statement.register
    def _(self, stmt: ast.WhileStatement) -> None:
        self.resolve_expression(stmt.condition)
        self.resolve_statement(stmt.body)

    @resolve_statement.register
    def _(self, stmt: ast.ReturnStatement) -> None:
        return_type = self.resolve_expression(stmt.expr)
        if not self._expected_return_types[0].can_assign(return_type):
            raise Exception("Invalid return type")

    @resolve_statement.register
    def _(self, stmt: ast.ExpressionStatement) -> None:
        self.resolve_expression(stmt.expr)

    @singledispatchmethod
    def resolve_expression(self, expr: ast.Expression) -> types.Type:
        raise NotImplementedError()

    @resolve_expression.register
    def _(self, expr: ast.IntLiteralExpression) -> types.Type:
        return types.int_type

    @resolve_expression.register
    def _(self, expr: ast.RationalLiteralExpression) -> types.Type:
        return types.ratio_type

    @resolve_expression.register
    def _(self, expr: ast.StringLiteralExpression) -> types.Type:
        return types.str_type

    @resolve_expression.register
    def _(self, expr: ast.BooleanLiteralExpression) -> types.Type:
        return types.bool_type

    @resolve_expression.register
    def _(self, expr: ast.NoneLiteralExpression) -> types.Type:
        return types.none_type

    @resolve_expression.register
    def _(self, expr: ast.VariableExpression) -> types.Type:
        if res := self._scope.get(expr.identifier.name):
            var_type, dist = res
            logger.debug(f"Resolved variable '{expr.identifier.name}': {var_type=} and {dist=}")
            expr.scope_distance = dist
            return var_type

        raise Exception(f"No variable named {expr.identifier.name}")

    @resolve_expression.register
    def _(self, expr: ast.GroupExpression) -> types.Type:
        return self.resolve_expression(expr.expr)

    @resolve_expression.register
    def _(self, expr: ast.UnaryExpression) -> types.Type:
        right = self.resolve_expression(expr.right)

        match expr.operator:
            case tokens.BangToken():
                if right == types.bool_type:
                    return right

            case tokens.MinusToken():
                if right in (types.int_type, types.ratio_type):
                    return right

            case _:
                raise Exception("invalid unary operator?")

        raise Exception(f"cannot apply operator {expr.operator} on type {right}")

    @resolve_expression.register
    def _(self, expr: ast.BinaryExpression) -> types.Type:
        left = self.resolve_expression(expr.left)
        right = self.resolve_expression(expr.right)

        if left == types.int_type and right == types.ratio_type:
            left = types.ratio_type
        if left == types.ratio_type and right == types.int_type:
            right = types.ratio_type

        match expr.operator:
            case tokens.AndToken() | tokens.OrToken():
                return left.get_common_ancestor(right)

            case tokens.EqualEqualToken() | tokens.BangEqualToken():
                return types.bool_type

            case tokens.GreaterToken() | tokens.GreaterEqualToken() | tokens.LessToken() | tokens.LessEqualToken() | tokens.MinusToken() | tokens.StarToken() | tokens.SlashToken():
                if left == right and left in (types.int_type, types.ratio_type):
                    return left

            case tokens.PlusToken():
                if left == right and left in (types.int_type, types.ratio_type, types.str_type):
                    return left

            case _:
                raise Exception("invalid binary operator?")

        raise Exception(f"cannot apply operator {expr.operator} on types {left} and {right}")

    @resolve_expression.register
    def _(self, expr: ast.VariableAssignment) -> types.Type:
        if res := self._scope.get(expr.name.name):
            var_type, dist = res

            expression_type = self.resolve_expression(expr.expr)
            if not var_type.can_assign(expression_type):
                raise Exception(f"cannot assign type {expression_type} to a {var_type} variable")

            logger.debug(f"Resolved variable '{expr.name.name}': {var_type=} and {dist=}")
            expr.scope_distance = dist
            return var_type

        raise Exception(f"No variable named {expr.name}")

    @resolve_expression.register
    def _(self, expr: ast.FunctionCall) -> types.Type:
        func_type = self.resolve_expression(expr.expr)
        if not isinstance(func_type, types.FunctionType):
            raise Exception("tried to call a non-function variable")

        argument_types = [self.resolve_expression(arg) for arg in expr.arguments]
        if not func_type.can_call(argument_types):
                raise Exception(f"Invalid types")

        return func_type.return_type
