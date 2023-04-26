from dataclasses import dataclass
import logging
from typing import ClassVar
import tree_sitter

from . import types


logger = logging.getLogger(__name__)


@dataclass
class State:
    has_errors: bool = False


class Node:
    _cache: ClassVar[dict[int, "Node"]] = {}

    def __init__(self, ts_node: tree_sitter.Node, state: State):
        self._inner = ts_node
        self._state = state

        self._scope_distance: int | None = None
        self._func_type: types.FunctionType | None = None

        self._report_errors()

    @classmethod
    def get_or_create(cls, ts_node: tree_sitter.Node, state: State) -> "Node":
        if ts_node.id not in cls._cache:
            cls._cache[ts_node.id] = cls(ts_node, state)
        return cls._cache[ts_node.id]

    def __repr__(self) -> str:
        return repr(self._inner)

    def __str__(self) -> str:
        return str(self._inner)

    def _report_errors(self):
        errors = [
            child for child in self._inner.children
            if child.type == "ERROR"
        ]
        for error in errors:
            self._state.has_errors = True
            logger.error(f"Syntax error {error.start_point} - {error.end_point}: text {error.text}")

    @property
    def children(self) -> "list[Node]":
        return [Node.get_or_create(c, self._state) for c in self._inner.children]

    def get(self, field: str) -> "Node":
        if child := self._inner.child_by_field_name(field):
            return Node.get_or_create(child, self._state)
        raise Exception(f"Node {self} does not have field {field}")

    def get_or_none(self, field: str) -> "Node | None":
        if child := self._inner.child_by_field_name(field):
            return Node.get_or_create(child, self._state)
        return None

    def get_all(self, field: str) -> "list[Node]":
        return [Node.get_or_create(c, self._state) for c in self._inner.children_by_field_name(field)]

    @property
    def text(self) -> str:
        return self._inner.text.decode("utf-8")

    @property
    def type(self) -> str:
        return self._inner.type

    @property
    def start_point(self) -> tuple[int, int]:
        return self._inner.start_point

    @property
    def end_point(self) -> tuple[int, int]:
        return self._inner.end_point

    @property
    def scope_distance(self) -> int:
        if self._scope_distance is None:
            raise Exception(f"No scope distance for node {self}")
        return self._scope_distance

    @scope_distance.setter
    def scope_distance(self, value: int) -> None:
        self._scope_distance = value

    @property
    def func_type(self) -> types.FunctionType:
        if self._func_type is None:
            raise Exception(f"No func type for node {self}")
        return self._func_type

    @func_type.setter
    def func_type(self, value) -> None:
        self._func_type = value
