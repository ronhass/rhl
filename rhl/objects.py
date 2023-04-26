from abc import ABC, abstractmethod
from typing import Callable, ClassVar
from dataclasses import dataclass

from . import types


@dataclass
class Object(ABC):
    type: ClassVar[types.Type] = types.any_type

    @abstractmethod
    def to_string(self) -> str:
        pass


@dataclass
class IntObject(Object):
    value: int
    type: ClassVar[types.Type] = types.int_type

    def to_rational(self):
        return RationalObject(value=float(self.value))

    def to_string(self):
        return str(self.value)


@dataclass
class RationalObject(Object):
    value: float
    type: ClassVar[types.Type] = types.ratio_type

    def to_string(self):
        return str(self.value)


@dataclass
class StringObject(Object):
    value: str
    type: ClassVar[types.Type] = types.str_type

    def to_string(self):
        return str(self.value)


@dataclass
class BooleanObject(Object):
    value: bool
    type: ClassVar[types.Type] = types.bool_type

    def to_string(self):
        return "true" if self.value else "false"


class NoneObject(Object):
    type: ClassVar[types.Type] = types.none_type

    def to_string(self):
        return "none"


@dataclass
class FunctionObject(Object):
    name: str
    parameters: list[str]
    func_type: types.FunctionType

    closure: "environment.Environment"
    execute: Callable[["environment.Environment"], None]

    @property
    def type(self):
        return self.func_type

    def to_string(self):
        return f"func {self.name}"


@dataclass
class ListObject(Object):
    value: list[Object]
    element_type: types.Type

    @property
    def type(self):
        return types.ListType.get_or_create(self.element_type)

    def to_string(self):
        return "[{}]".format(", ".join([elem.to_string() for elem in self.value]))
