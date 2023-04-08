from . import objects, tokens, exceptions


class Environment:
    _BUILTINS: dict[str, objects.Object] = {}

    def __init__(self):
        self._stack: list[dict[str, objects.Object]] = [self._BUILTINS.copy()]

    def push(self) -> None:
        self._stack.insert(0, {})

    def pop(self) -> None:
        self._stack.pop(0)

    def get(self, identifier: tokens.IdentifierToken) -> objects.Object:
        for env in self._stack:
            if identifier.name in env:
                return env[identifier.name]
        raise exceptions.RHLRuntimeError(f"no variable named {identifier.name}", identifier.line + 1, identifier.column)

    def set(self, identifier: tokens.IdentifierToken, value: objects.Object) -> objects.Object:
        for env in self._stack:
            if identifier.name in env:
                original_value = env[identifier.name]

                if isinstance(original_value, objects.RationalObject) and isinstance(value, objects.IntObject):
                    value = value.to_rational()

                if type(value) != type(original_value):
                    raise exceptions.RHLRuntimeError(f"cannot assign {value.type_name()} value to a {original_value.type_name()} variable", identifier.line + 1, identifier.column)

                env[identifier.name] = value
                return value

        raise exceptions.RHLRuntimeError(f"no variable named {identifier.name} (use ':=' for decleration)", identifier.line + 1, identifier.column)

    def declare(self, name: str, value: objects.Object, stmt_type: tokens.IdentifierToken | None):
        if stmt_type is None:
            self._stack[0][name] = value
            return

        if stmt_type.name == objects.RationalObject.type_name() and isinstance(value, objects.IntObject):
            value = value.to_rational()

        for object_type in objects.Object.__subclasses__():
            if stmt_type.name == object_type.type_name():
                if not isinstance(value, object_type):
                    raise exceptions.RHLRuntimeError(f"could not assign {value.type_name()} value to a {object_type.type_name()} variable", stmt_type.line + 1, stmt_type.column)
                self._stack[0][name] = value
                return

        raise exceptions.RHLRuntimeError(f"invalid type {stmt_type.name}", stmt_type.line + 1, stmt_type.column)

    def __str__(self) -> str:
        return str(self._stack)
