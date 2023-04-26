from functools import singledispatchmethod
from typing import NoReturn, cast
from . import objects, exceptions, types, node
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

    def _raise_exception(self, message: str, node: node.Node) -> NoReturn:
        raise exceptions.RHLRuntimeError(message, node)

    def execute(self, node: node.Node) -> None:
        execute_func = getattr(self, f'_execute_{node.type}', None)
        if not execute_func:
            self._raise_exception(f"Invalid statement node {node.type}", node)
        execute_func(node)

    def _execute_source_file(self, node: node.Node) -> None:
        for child in node.children:
            self.execute(child)

    def _execute_function_declaration(self, node: node.Node) -> None:
        func = objects.FunctionObject(
            name=node.get('name').text,
            parameters=[
                param.get('name').text for param in node.get_all('parameter')
            ],
            func_type=node.func_type,
            closure=Environment(self.environment),
            execute=lambda env: Interpreter(env).execute(node.get('body')),
        )
        self.environment.declare(node.get('name').text, func)

    def _execute_block(self, node: node.Node) -> None:
        for _stmt in node.children[1:-1]:  # TODO: better block grammar?
            self.execute(_stmt)

    def _execute_if(self, node: node.Node) -> None:
        condition = self.evaluate(node.get('condition'))
        if self._is_truthy(condition):
            self.execute(node.get('body'))
        elif (else_body := node.get_or_none('else_body')) is not None:
            self.execute(else_body)

    def _execute_while(self, node: node.Node) -> None:
        while self._is_truthy(self.evaluate(node.get('condition'))):
            self.execute(node.get('body'))

    def _execute_return(self, node: node.Node) -> None:
        value = self.evaluate(node.get('expression'))
        raise self.Return(value)

    def _execute_expression_statement(self, node: node.Node) -> None:
        self.evaluate(node.get('expression'))

    def evaluate(self, node: node.Node) -> objects.Object:
        evaluate_func = getattr(self, f'_evaluate_{node.type}', None)
        if not evaluate_func:
            self._raise_exception(f"Invalid expression node", node)
        return evaluate_func(node)

    def _evaluate_integer(self, node: node.Node) -> objects.IntObject:
        return objects.IntObject(value=int(node.text))

    def _evaluate_rational(self, node: node.Node) -> objects.RationalObject:
        return objects.RationalObject(value=float(node.text))

    def _evaluate_string(self, node: node.Node) -> objects.StringObject:
        return objects.StringObject(value=node.text[1:-1])

    def _evaluate_boolean(self, node: node.Node) -> objects.BooleanObject:
        return objects.BooleanObject(value=bool(node.text))

    def _evaluate_none(self, _: node.Node) -> objects.NoneObject:
        return objects.NoneObject()

    def _evaluate_identifier(self, node: node.Node) -> objects.Object:
        return self.environment.get_at(node.text, node.scope_distance)

    def _evaluate_call(self, node: node.Node) -> objects.Object:
        func = self.evaluate(node.get('function'))
        func = cast(objects.FunctionObject, func)

        env = Environment(func.closure)
        env.push()
        for param, arg in zip(func.parameters, node.get_all('argument')):
            env.declare(param, self.evaluate(arg))

        try:
            func.execute(env)
        except self.Return as ex:
            return ex.value

        return objects.NoneObject()

    def _evaluate_variable_declaration(self, node: node.Node) -> objects.Object:
        value = self.evaluate(node.get('value'))
        self.environment.declare(node.get('name').text, value)
        return value

    def _evaluate_variable_assignment(self, node: node.Node) -> objects.Object:
        value = self.evaluate(node.get('value'))
        self.environment.set_at(node.get('name').text, node.scope_distance, value)
        return value

    def _evaluate_group(self, node: node.Node) -> objects.Object:
        return self.evaluate(node.get('expression'))

    def _evaluate_unary_expression(self, node: node.Node) -> objects.Object:
        right = self.evaluate(node.get('right'))
        operator = node.get('operator').text

        match operator:
            case '!':
                if isinstance(right, objects.BooleanObject):
                    return objects.BooleanObject(value=not right.value)

            case '-':
                if isinstance(right, objects.IntObject):
                    return objects.IntObject(value=-right.value)
                if isinstance(right, objects.RationalObject):
                    return objects.RationalObject(value=-right.value)

            case _:
                raise Exception("invalid unary operator")

        self._raise_exception(f"cannot apply operator {operator} on {right.type}", node)
            
    def _evaluate_binary_expression(self, node: node.Node) -> objects.Object:
        operator = node.get('operator').text

        match operator:
            case 'and':
                if not self._is_truthy(left := self.evaluate(node.get('left'))):
                    return left
                return self.evaluate(node.get('right'))

            case 'or':
                if self._is_truthy(left := self.evaluate(node.get('left'))):
                    return left
                return self.evaluate(node.get('right'))

        left = self.evaluate(node.get('left'))
        right = self.evaluate(node.get('right'))

        # convert int to rational if necessary
        if isinstance(left, objects.IntObject) and isinstance(right, objects.RationalObject):
            left = left.to_rational()
        if isinstance(left, objects.RationalObject) and isinstance(right, objects.IntObject):
            right = right.to_rational()

        def _check_types(class_or_tuple) -> bool:
            return isinstance(left, class_or_tuple) and isinstance(right, class_or_tuple)

        match operator:
            case '==':
                return objects.BooleanObject(value=left.value == right.value)

            case '!=':
                return objects.BooleanObject(value=left.value != right.value)

            case '>':
                if _check_types((objects.IntObject, objects.RationalObject)):
                    return objects.BooleanObject(value=left.value > right.value)

            case '>=':
                if _check_types((objects.IntObject, objects.RationalObject)):
                    return objects.BooleanObject(value=left.value >= right.value)

            case '<':
                if _check_types((objects.IntObject, objects.RationalObject)):
                    return objects.BooleanObject(value=left.value < right.value)

            case '<=':
                if _check_types((objects.IntObject, objects.RationalObject)):
                    return objects.BooleanObject(value=left.value <= right.value)

            case '+':
                if _check_types(objects.IntObject):
                    return objects.IntObject(value=left.value + right.value)
                if _check_types(objects.RationalObject):
                    return objects.RationalObject(value=left.value + right.value)
                if _check_types(objects.StringObject):
                    return objects.StringObject(value=left.value + right.value)

            case '-':
                if _check_types(objects.IntObject):
                    return objects.IntObject(value=left.value - right.value)
                if _check_types(objects.RationalObject):
                    return objects.RationalObject(value=left.value - right.value)

            case '*':
                if _check_types(objects.IntObject):
                    return objects.IntObject(value=left.value * right.value)
                if _check_types(objects.RationalObject):
                    return objects.RationalObject(value=left.value * right.value)

            case '/':
                try:
                    if _check_types(objects.IntObject):
                        return objects.IntObject(value=left.value // right.value)
                    if _check_types(objects.RationalObject):
                        return objects.RationalObject(value=left.value / right.value)
                except ZeroDivisionError:
                    raise exceptions.RHLDivisionByZeroError(node)

            case _:
                raise Exception(f"Invalid binary operator {operator}")

        self._raise_exception(f"cannot apply operator {operator} on {left.type} and {right.type}", node)

    def _evaluate_list(self, node: node.Node) -> objects.Object:
        items = [self.evaluate(item) for item in node.get_all('value')]
        # TODO: determine the type in the resolver
        if len(items) == 0:
            return objects.ListObject(element_type=types.any_type, value=[])
        return objects.ListObject(element_type=items[0].type, value=items)


    def _evaluate_get_item(self, node: node.Node) -> objects.Object:
        left = self.evaluate(node.get('left'))
        left = cast(objects.ListObject, left)

        index = self.evaluate(node.get('index'))
        index = cast(objects.IntObject, index)

        return left.value[index.value]
