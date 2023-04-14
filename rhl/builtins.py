from typing import Callable
from . import environment, scope, interpreter, objects


def register_builtin(func: Callable):
    name = func.__name__
    if name.startswith("__rhl_"):
        name = name[len("__rhl_"):]

    annotations = func.__annotations__.copy()
    return_type = annotations.pop("return").type
    parameters = [(param_name, param_type.type) for param_name, param_type in annotations.items()]

    def _func(env: environment.Environment) -> None:
        kwargs = {arg: env.get_at(arg, 0) for arg in annotations.keys()}
        raise interpreter.Interpreter.Return(func(**kwargs))
            
    func_obj = objects.FunctionObject(
        name=name,
        parameters=parameters,
        return_type=return_type,
        closure=environment.GLOBAL_ENV,
        execute=_func
    )
    environment.GLOBAL_ENV.declare(name, func_obj)
    scope.GLOBAL_SCOPE.declare(name, func_obj.type)
    return _func


@register_builtin
def __rhl_print(obj: objects.Object) -> objects.NoneObject:
    print(obj.to_string())
    return objects.NoneObject()


@register_builtin
def __rhl_str(obj: objects.Object) -> objects.StringObject:
    return objects.StringObject(value=obj.to_string())


@register_builtin
def __rhl_type(obj: objects.Object) -> objects.StringObject:
    return objects.StringObject(value=obj.type.name)
