from functools import singledispatchmethod
from typing import cast
from . import ast, objects, tokens, exceptions
from .environment import Environment, GLOBAL_ENV


class Interpreter:
    class Return(Exception):
        def __init__(self, value: objects.Object):
            self.value = value

    def __init__(self, env: Environment | None = None):
        if env:
            self.environment = env
        else:
            self.environment = Environment(GLOBAL_ENV)
            self.environment.push()

    def _is_truthy(self, object: objects.Object):
        if isinstance(object, objects.NoneObject):
            return False

        if isinstance(object, objects.BooleanObject):
            return object.value

        # TODO: "" should be false or true?
        return True

    @singledispatchmethod
    def execute(self, stmt: ast.Statement) -> None:
        raise NotImplementedError()

    @execute.register
    def _(self, stmt: ast.Program) -> None:
        for _stmt in stmt.statements:
            self.execute(_stmt)

    @execute.register
    def _(self, stmt: ast.VarDeclaration) -> None:
        value = self.evaluate(stmt.expr)
        self.environment.declare(stmt.name.name, value)

    @execute.register
    def _(self, stmt: ast.FunDeclaration) -> None:
        func = objects.FunctionObject(
            name=stmt.name.name,
            parameters=[(token.name, _type) for token, _type in stmt.parameters],
            return_type=stmt.return_type,
            closure=Environment(self.environment),
            execute=lambda env: Interpreter(env).execute(stmt.body),
        )
        self.environment.declare(stmt.name.name, func)

    @execute.register
    def _(self, stmt: ast.Block) -> None:
        for _stmt in stmt.statements:
            self.execute(_stmt)

    @execute.register
    def _(self, stmt: ast.IfStatement) -> None:
        condition = self.evaluate(stmt.condition)
        if self._is_truthy(condition):
            self.execute(stmt.body)
        elif stmt.else_body is not None:
            self.execute(stmt.else_body)

    @execute.register
    def _(self, stmt: ast.WhileStatement) -> None:
        while self._is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.body)

    @execute.register
    def _(self, stmt: ast.ReturnStatement) -> None:
        value = self.evaluate(stmt.expr)
        raise self.Return(value)

    @execute.register
    def _(self, stmt: ast.ExpressionStatement) -> None:
        self.evaluate(stmt.expr)

    @singledispatchmethod
    def evaluate(self, expr: ast.Expression) -> objects.Object:
        raise NotImplementedError()

    @evaluate.register
    def _(self, expr: ast.IntLiteralExpression) -> objects.IntObject:
        return objects.IntObject(value=expr.value)

    @evaluate.register
    def _(self, expr: ast.RationalLiteralExpression) -> objects.RationalObject:
        return objects.RationalObject(value=expr.value)

    @evaluate.register
    def _(self, expr: ast.StringLiteralExpression) -> objects.StringObject:
        return objects.StringObject(value=expr.value)

    @evaluate.register
    def _(self, expr: ast.BooleanLiteralExpression) -> objects.BooleanObject:
        return objects.BooleanObject(value=expr.value)

    @evaluate.register
    def _(self, expr: ast.NoneLiteralExpression) -> objects.NoneObject:
        return objects.NoneObject()

    @evaluate.register
    def _(self, expr: ast.VariableExpression) -> objects.Object:
        return self.environment.get_at(expr.identifier.name, expr.scope_distance)

    @evaluate.register
    def _(self, expr: ast.FunctionCall) -> objects.Object:
        func = self.evaluate(expr.expr)
        func = cast(objects.FunctionObject, func)

        env = Environment(func.closure)
        env.push()
        for param, arg in zip(func.parameters, expr.arguments):
            param_name, _ = param
            env.declare(param_name, self.evaluate(arg))

        try:
            func.execute(env)
        except self.Return as ex:
            return ex.value

        return objects.NoneObject()

    @evaluate.register
    def _(self, expr: ast.VariableAssignment) -> objects.Object:
        value = self.evaluate(expr.expr)
        self.environment.set_at(expr.name.name, expr.scope_distance, value)
        return value

    @evaluate.register
    def _(self, expr: ast.GroupExpression) -> objects.Object:
        return self.evaluate(expr.expr)

    @evaluate.register
    def _(self, expr: ast.UnaryExpression) -> objects.Object:
        right = self.evaluate(expr.right)

        match expr.operator:
            case tokens.BangToken():
                if isinstance(right, objects.BooleanObject):
                    return objects.BooleanObject(value=not right.value)

            case tokens.MinusToken():
                if isinstance(right, objects.IntObject):
                    return objects.IntObject(value=-right.value)
                if isinstance(right, objects.RationalObject):
                    return objects.RationalObject(value=-right.value)

            case _:
                raise Exception("invalid unary operator?")

        raise exceptions.RHLRuntimeError(f"cannot apply operator {expr.operator} on {right.type}", expr.operator.line + 1, expr.operator.column)
            
    @evaluate.register
    def _(self, expr: ast.BinaryExpression) -> objects.Object:
        match expr.operator:
            case tokens.AndToken():
                if not self._is_truthy(left := self.evaluate(expr.left)):
                    return left
                return self.evaluate(expr.right)

            case tokens.OrToken():
                if self._is_truthy(left := self.evaluate(expr.left)):
                    return left
                return self.evaluate(expr.right)

        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        # convert int to rational if necessary
        if isinstance(left, objects.IntObject) and isinstance(right, objects.RationalObject):
            left = left.to_rational()
        if isinstance(left, objects.RationalObject) and isinstance(right, objects.IntObject):
            right = right.to_rational()

        def _check_types(class_or_tuple) -> bool:
            return isinstance(left, class_or_tuple) and isinstance(right, class_or_tuple)

        match expr.operator:
            case tokens.EqualEqualToken():
                return objects.BooleanObject(value=left.value == right.value)

            case tokens.BangEqualToken():
                return objects.BooleanObject(value=left.value != right.value)

            case tokens.GreaterToken():
                if _check_types((objects.IntObject, objects.RationalObject)):
                    return objects.BooleanObject(value=left.value > right.value)

            case tokens.GreaterEqualToken():
                if _check_types((objects.IntObject, objects.RationalObject)):
                    return objects.BooleanObject(value=left.value >= right.value)

            case tokens.LessToken():
                if _check_types((objects.IntObject, objects.RationalObject)):
                    return objects.BooleanObject(value=left.value < right.value)

            case tokens.LessEqualToken():
                if _check_types((objects.IntObject, objects.RationalObject)):
                    return objects.BooleanObject(value=left.value <= right.value)

            case tokens.PlusToken():
                if _check_types(objects.IntObject):
                    return objects.IntObject(value=left.value + right.value)
                if _check_types(objects.RationalObject):
                    return objects.RationalObject(value=left.value + right.value)
                if _check_types(objects.StringObject):
                    return objects.StringObject(value=left.value + right.value)

            case tokens.MinusToken():
                if _check_types(objects.IntObject):
                    return objects.IntObject(value=left.value - right.value)
                if _check_types(objects.RationalObject):
                    return objects.RationalObject(value=left.value - right.value)

            case tokens.StarToken():
                if _check_types(objects.IntObject):
                    return objects.IntObject(value=left.value * right.value)
                if _check_types(objects.RationalObject):
                    return objects.RationalObject(value=left.value * right.value)

            case tokens.SlashToken():
                try:
                    if _check_types(objects.IntObject):
                        return objects.IntObject(value=left.value // right.value)
                    if _check_types(objects.RationalObject):
                        return objects.RationalObject(value=left.value / right.value)
                except ZeroDivisionError:
                    raise exceptions.RHLDivisionByZeroError(expr.operator.line + 1, expr.operator.column)

            case _:
                raise Exception(f"Invalid binary operator {expr.operator}")

        raise exceptions.RHLRuntimeError(f"cannot apply operator {expr.operator} on {left.type} and {right.type}", expr.operator.line + 1, expr.operator.column)
