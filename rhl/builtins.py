from typing import Callable, Optional
from . import environment, scope, interpreter, objects, types, qsim


def register_builtin(
    name: Optional[str] = None,
    parameters: Optional[list[tuple[str, types.Type]]] = None,
    return_type: Optional[types.Type] = None,
):
    def decorator(func: Callable):
        _name = name
        _return_type = return_type
        _parameters = parameters

        if _name is None:
            _name = func.__name__
            if _name.startswith("__rhl_"):
                _name = _name[len("__rhl_") :]

        annotations = func.__annotations__.copy()
        qsim = annotations.pop("qsim", None)

        annotated_return = annotations.pop("return")
        if _return_type is None:
            _return_type = annotated_return.type
        if _parameters is None:
            _parameters = [
                (param_name, param_type.type)
                for param_name, param_type in annotations.items()
            ]
        _params_names = [param_name for param_name, _ in _parameters]
        _params_types = [param_type for _, param_type in _parameters]

        def _func(env: environment.Environment) -> None:
            kwargs = {arg: env.get_at(arg, 0) for arg in annotations.keys()}
            if qsim:
                kwargs["qsim"] = env.get_at("qsim", 1)
            raise interpreter.Interpreter.Return(func(**kwargs))

        func_type = types.FunctionType.get_or_create(
            params_types=_params_types, return_type=_return_type
        )

        func_obj = objects.FunctionObject(
            name=_name,
            parameters=_params_names,
            func_type=func_type,
            closure=environment.GLOBAL_ENV,
            execute=_func,
        )
        environment.GLOBAL_ENV.declare(_name, func_obj)
        scope.GLOBAL_SCOPE.declare(_name, func_obj.type)
        return _func

    return decorator


@register_builtin()
def __rhl_print(obj: objects.Object) -> objects.NoneObject:
    print(obj.to_string())
    return objects.NoneObject()


@register_builtin()
def __rhl_str(obj: objects.Object) -> objects.StringObject:
    return objects.StringObject(value=obj.to_string())


@register_builtin()
def __rhl_type(obj: objects.Object) -> objects.StringObject:
    return objects.StringObject(value=obj.type.name)


@register_builtin(
    return_type=types.ListType.get_or_create(element_type=types.int_type),
)
def __rhl_range(obj: objects.IntObject) -> objects.ListObject:
    return objects.ListObject(
        value=[objects.IntObject(value=v) for v in range(obj.value)],
        element_type=types.int_type,
    )


@register_builtin(
    parameters=[("obj", types.ListType.get_or_create(element_type=types.any_type))],
)
def __rhl_len(obj: objects.ListObject) -> objects.IntObject:
    return objects.IntObject(value=len(obj.value))


@register_builtin(
    parameters=[
        ("l", types.ListType.get_or_create(element_type=types.int_type)),
        ("v", types.int_type),
    ]
)
def __rhl_append(l: objects.ListObject, v: objects.IntObject) -> objects.NoneObject:
    l.value.append(v)
    return objects.NoneObject()


@register_builtin(
    return_type=types.ListType.get_or_create(element_type=types.qubit_type),
)
def __rhl_qalloc(qsim: qsim.QSimulator, obj: objects.IntObject) -> objects.ListObject:
    qubits = qsim.qalloc(obj.value)
    return objects.ListObject(
        value=[objects.QubitObject(value=v) for v in qubits],
        element_type=types.qubit_type,
    )


@register_builtin(
    parameters=[
        ("qubits", types.ListType.get_or_create(element_type=types.qubit_type)),
    ]
)
def __rhl_qfree(qsim: qsim.QSimulator, qubits: objects.ListObject) -> objects.NoneObject:
    qsim.qfree([obj.value for obj in qubits.value])
    return objects.NoneObject()


@register_builtin()
def __rhl_measure(qsim: qsim.QSimulator, qubit: objects.QubitObject) -> objects.IntObject:
    return objects.IntObject(value=qsim.measure(qubit.value))


@register_builtin()
def __rhl_x(qsim: qsim.QSimulator, qubit: objects.QubitObject) -> objects.NoneObject:
    qsim.x(qubit.value)
    return objects.NoneObject()


@register_builtin()
def __rhl_h(qsim: qsim.QSimulator, qubit: objects.QubitObject) -> objects.NoneObject:
    qsim.h(qubit.value)
    return objects.NoneObject()


@register_builtin()
def __rhl_cx(qsim: qsim.QSimulator, control: objects.QubitObject, target: objects.QubitObject) -> objects.NoneObject:
    qsim.cx(control.value, target.value)
    return objects.NoneObject()


@register_builtin(
    parameters=[
        ("qubits", types.ListType.get_or_create(element_type=types.qubit_type)),
    ]
)
def __rhl_mcz(qsim: qsim.QSimulator, qubits: objects.ListObject) -> objects.NoneObject:
    qsim.mcz([obj.value for obj in qubits.value])
    return objects.NoneObject()
