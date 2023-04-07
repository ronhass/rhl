from typing import Any
from dataclasses import dataclass


@dataclass
class Object:
    value: Any

    @staticmethod
    def type_name():
        return "object"

@dataclass
class IntObject(Object):
    value: int

    def to_rational(self):
        return RationalObject(value=float(self.value))

    @staticmethod
    def type_name():
        return "int"


@dataclass
class RationalObject(Object):
    value: float

    @staticmethod
    def type_name():
        return "rational"


@dataclass
class StringObject(Object):
    value: str

    @staticmethod
    def type_name():
        return "str"


@dataclass
class BooleanObject(Object):
    value: bool

    @staticmethod
    def type_name():
        return "bool"


@dataclass
class NoneObject(Object):
    value: None = None

    @staticmethod
    def type_name():
        return "none"
