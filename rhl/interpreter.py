from functools import singledispatchmethod
from . import ast, objects, tokens, exceptions


class Interpreter:
    def __init__(self, root: ast.Program):
        self.root = root
        self.environment: dict[str, objects.Object] = {}

    def interpret(self):
        for stmt in self.root.statements:
            self.execute(stmt)

    @singledispatchmethod
    def execute(self, stmt: ast.Statement) -> None:
        raise NotImplementedError()

    @execute.register
    def _(self, stmt: ast.Decleration) -> None:
        value = self.evaluate(stmt.expr)
        if stmt.type is None:
            self.environment[stmt.name.name] = value
            return

        if stmt.type.name == objects.RationalObject.type_name() and isinstance(value, objects.IntObject):
            value = value.to_rational()

        for object_type in objects.Object.__subclasses__():
            if stmt.type.name == object_type.type_name():
                if not isinstance(value, object_type):
                    raise exceptions.RHLRuntimeError(f"could not assign {value.type_name()} value to a {object_type.type_name()} variable", stmt.type.line + 1, stmt.type.column)
                self.environment[stmt.name.name] = value
                return

        raise exceptions.RHLRuntimeError(f"invalid type {stmt.type.name}", stmt.type.line + 1, stmt.type.column)

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

        raise exceptions.RHLRuntimeError(f"cannot apply operator {expr.operator} on {right.type_name()}", expr.operator.line + 1, expr.operator.column)
            
    @evaluate.register
    def _(self, expr: ast.BinaryExpression) -> objects.Object:
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
                raise Exception("Invalid binary operator?")

        raise exceptions.RHLRuntimeError(f"cannot apply operator {expr.operator} on {left.type_name()} and {right.type_name()}", expr.operator.line + 1, expr.operator.column)
