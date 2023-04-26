from dataclasses import dataclass
import logging
from typing import ClassVar


logger = logging.getLogger(__name__)


@dataclass
class Type:
    name: str
    parent: "Type | None"

    def __eq__(self, other: "Type") -> bool:
        return self.name == other.name

    def __repr__(self) -> str:
        return self.name

    def is_ancestor_of(self, other: "Type | None") -> bool:
        while other:
            if self == other:
                return True
            other = other.parent
        return False

    def get_common_ancestor(self, other: "Type") -> "Type":
        if self.is_ancestor_of(other):
            return self
        if other.is_ancestor_of(self):
            return other

        if self.parent is None and other.parent is None:
            raise Exception("No common ancestor")

        parent_or_self = self.parent or self
        parent_or_other = other.parent or other
        return parent_or_self.get_common_ancestor(parent_or_other)

    def can_assign(self, other: "Type") -> bool:
        return self.is_ancestor_of(other)


any_type = Type("any", None)
ratio_type = Type("ratio", any_type)
int_type = Type("int", ratio_type)
str_type = Type("str", any_type)
bool_type = Type("bool", any_type)
none_type = Type("none", any_type)

basic_types = [
    any_type,
    int_type,
    ratio_type,
    str_type,
    bool_type,
    none_type,
]

basic_types_names = {_type.name: _type for _type in basic_types}


@dataclass
class FunctionType(Type):
    params_types: list[Type]
    return_type: Type

    _cache: ClassVar[dict[str, "FunctionType"]] = {}

    @classmethod
    def get_or_create(cls, params_types: list[Type], return_type: Type):
        name = "func[[{}],{}]".format(
            ",".join([_type.name for _type in params_types]), return_type.name
        )
        if name not in cls._cache:
            logger.debug(f"Creating new function type: '{name}'")
            cls._cache[name] = cls(name, any_type, params_types, return_type)
        return cls._cache[name]

    def can_call(self, arg_types: list[Type]) -> bool:
        if len(arg_types) != len(self.params_types):
            return False

        for arg_type, param_type in zip(arg_types, self.params_types):
            if not param_type.can_assign(arg_type):
                return False

        return True

    def can_assign(self, other: Type):
        if not isinstance(other, FunctionType):
            return False

        if not self.return_type.is_ancestor_of(other.return_type):
            return False

        if len(self.params_types) != len(other.params_types):
            return False

        for self_param_type, other_param_type in zip(
            self.params_types, other.params_types
        ):
            if not other_param_type.is_ancestor_of(self_param_type):
                return False

        return True


@dataclass
class ListType(Type):
    element_type: Type

    _cache: ClassVar[dict[str, "ListType"]] = {}

    @classmethod
    def get_or_create(cls, element_type: Type) -> "ListType":
        name = f"list[{element_type}]"
        if name not in cls._cache:
            logger.debug(f"Creating new list type: '{name}'")
            cls._cache[name] = cls(name, any_type, element_type)
        return cls._cache[name]

    def get_common_ancestor(self, other: Type) -> Type:
        if not isinstance(other, ListType):
            return super().get_common_ancestor(other)
        return self.element_type.get_common_ancestor(other.element_type)

    def can_assign(self, other: Type) -> bool:
        if not isinstance(other, ListType):
            return False
        return self.element_type.can_assign(other.element_type)
