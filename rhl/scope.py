from . import types


class Scope:
    def __init__(self) -> None:
        self._stack: list[dict[str, types.Type]] = [{}]

    def push(self) -> None:
        self._stack.insert(0, {})

    def pop(self) -> None:
        self._stack.pop(0)

    def get(self, name: str) -> tuple[types.Type, int] | None:
        for index, scope in enumerate(self._stack):
            if name in scope:
                return (scope[name], index)
        return None

    def declare(self, name: str, _type: types.Type) -> None:
        if name in self._stack[0]:
            raise Exception(f"{name} already declared in the current scope")
        self._stack[0][name] = _type


GLOBAL_SCOPE = Scope()
