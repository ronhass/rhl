from . import environment, scope, interpreter, objects, types


def register_builtin(name: str, parameters: list[tuple[str, types.Type]], return_type: types.Type):
    def decorator(func):
        func_obj = objects.FunctionObject(
            name=name,
            parameters=parameters,
            return_type=return_type,
            closure=environment.GLOBAL_ENV,
            execute=func
        )
        environment.GLOBAL_ENV.declare(name, func_obj)
        scope.GLOBAL_SCOPE.declare(name, func_obj.type)
        return func

    return decorator


@register_builtin(
    name="print",
    parameters=[("obj", types.any_type)],
    return_type=types.none_type,
)
def print_func_execute(env: environment.Environment) -> None:
    obj = env.get_at("obj", 0)
    print(obj.to_string())


@register_builtin(
    name="str",
    parameters=[("obj", types.any_type)],
    return_type=types.str_type,
)
def str_func_execute(env: environment.Environment) -> None:
    obj = env.get_at("obj", 0)
    raise interpreter.Interpreter.Return(objects.StringObject(value=obj.to_string()))


@register_builtin(
    name="type",
    parameters=[("obj", types.any_type)],
    return_type=types.str_type,
)
def type_func_execute(env: environment.Environment) -> None:
    obj = env.get_at("obj", 0)
    raise interpreter.Interpreter.Return(objects.StringObject(value=obj.type.name))
