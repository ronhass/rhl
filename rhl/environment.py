from . import objects


class Environment:
    def __init__(self, env: "Environment | None" = None):
        self._stack: list[dict[str, objects.Object]] = (
            env._stack.copy() if env else [{}]
        )

    def push(self) -> None:
        self._stack.insert(0, {})

    def pop(self) -> None:
        self._stack.pop(0)

    def get_at(self, name: str, distance: int) -> "objects.Object":
        if distance < 0:
            raise Exception("invalid distance")

        return self._stack[distance][name]

    def set_at(self, name: str, distance: int, value: "objects.Object") -> None:
        if distance < 0:
            raise Exception("invalid distance")

        self._stack[distance][name] = value

    def declare(self, name: str, value: "objects.Object") -> None:
        self.set_at(name, 0, value)

    def __str__(self) -> str:
        return "\n".join([str(d) for d in self._stack])


GLOBAL_ENV = Environment()
