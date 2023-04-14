from . import environment, scope, interpreter, objects, types

def print_func_execute(env: environment.Environment) -> None:
    obj = env.get_at("obj", 0)
    print(obj.to_string())


def type_func_execute(env: environment.Environment) -> None:
    obj = env.get_at("obj", 0)
    raise interpreter.Interpreter.Return(objects.StringObject(value=obj.type.name))

def init_builtins():
    print_func = objects.FunctionObject(
        name="print",
        parameters=[("obj", types.any_type)],
        return_type=types.none_type,
        closure=environment.GLOBAL_ENV,
        execute=print_func_execute,
    )

    environment.GLOBAL_ENV.declare("print", print_func)
    scope.GLOBAL_SCOPE.declare("print", print_func.type)

    type_func = objects.FunctionObject(
        name="type",
        parameters=[("obj", types.any_type)],
        return_type=types.str_type,
        closure=environment.GLOBAL_ENV,
        execute=type_func_execute,
    )

    environment.GLOBAL_ENV.declare("type", type_func)
    scope.GLOBAL_SCOPE.declare("type", type_func.type)
