import logging
from typing import NoReturn

from . import scope, types, node, exceptions


logger = logging.getLogger(__name__)


class Resolver:
    def __init__(self):
        self._scope = scope.GLOBAL_SCOPE
        self._scope.push()

        self._expected_return_types = []
        self._return_type_checked = []  # TODO: isn't really good...
        self._functions = []

    def _raise_exception(self, message: str, node: node.Node) -> NoReturn:
        raise exceptions.RHLResolverError(message, node)

    def _get_type(self, node: node.Node) -> types.Type:
        match node.type:
            case 'basic_type':
                return types.basic_types_names[node.text]
            case 'func_type':
                parameters = [
                    self._get_type(_t)
                    for _t in node.get_all('parameter_type')
                ]
                return_type = self._get_type(node.get('return_type'))
                return types.FunctionType.get_or_create(params_types=parameters, return_type=return_type)
            case 'list_type':
                element_type = node.get('element_type')
                return types.ListType.get_or_create(element_type=self._get_type(element_type))
            case _:
                self._raise_exception(f"Invalid type node", node)

    def visit(self, node: node.Node) -> None:
        visit_func = getattr(self, f'_visit_{node.type}', None)
        if not visit_func:
            self._raise_exception(f"Invalid statement node", node)
        visit_func(node)

    def _visit_source_file(self, node: node.Node) -> None:
        for child in node.children:
            self.visit(child)

    def _visit_function_declaration(self, node: node.Node) -> None:
        name = node.get('name').text
        logger.debug(f"Entering function '{name}'")
        self._functions.insert(0, name)

        params_names = [
            param.get('name').text for param in node.get_all('parameter')
        ]
        params_types = [
            self._get_type(param.get('type')) for param in node.get_all('parameter')
        ]

        if return_type_node := node.get_or_none('return_type'):
            return_type = self._get_type(return_type_node)
        else:
            return_type = types.none_type

        function_type = types.FunctionType.get_or_create(params_types=params_types, return_type=return_type)
        node.func_type = function_type

        self._scope.declare(name, function_type)

        self._scope.push()
        for param_name, param_type in zip(params_names, params_types):
            self._scope.declare(param_name, param_type)
        self._expected_return_types.insert(0, return_type)
        self._return_type_checked.insert(0, False)

        self.visit(node.get('body'))

        if not self._return_type_checked.pop(0) and return_type != types.none_type:
            self._raise_exception(f"Function didn't return a value", node)
        self._expected_return_types.pop(0)
        self._scope.pop()

        logger.debug(f"Exiting function '{name}'")
        self._functions.pop(0)

    def _visit_return(self, node: node.Node) -> None:
        return_type = self.resolve(node.get('expression'))
        if not self._expected_return_types[0].can_assign(return_type):
            self._raise_exception(f"Invalid return type inside function '{self._functions[0]}' (expectd {self._expected_return_types[0]}, got {return_type})", node)
        self._return_type_checked[0] = True

    def _visit_block(self, node: node.Node) -> None:
        for stmt in node.children[1:-1]:  # TODO: better block grammar?
            self.visit(stmt)

    def _visit_if(self, node: node.Node) -> None:
        self.resolve(node.get('condition'))
        self.visit(node.get('body'))
        if else_body := node.get_or_none('else_body'):
            self.visit(else_body)
    
    def _visit_while(self, node: node.Node) -> None:
        self.resolve(node.get('condition'))
        self.visit(node.get('body'))

    def _visit_expression_statement(self, node: node.Node) -> None:
        self.resolve(node.get('expression'))

    def resolve(self, node: node.Node) -> types.Type:
        resolve_func = getattr(self, f'_resolve_{node.type}', None)
        if not resolve_func:
            self._raise_exception(f"Invalid expression node", node)
        return resolve_func(node)

    def _resolve_integer(self, _: node.Node) -> types.Type:
        return types.int_type

    def _resolve_rational(self, _: node.Node) -> types.Type:
        return types.ratio_type

    def _resolve_string(self, _: node.Node) -> types.Type:
        return types.str_type

    def _resolve_boolean(self, _: node.Node) -> types.Type:
        return types.bool_type

    def _resolve_none(self, _: node.Node) -> types.Type:
        return types.none_type

    def _resolve_identifier(self, node: node.Node) -> types.Type:
        if res := self._scope.get(node.text):
            var_type, dist = res
            logger.debug(f"Resolved variable '{node.text}': {var_type=} and {dist=}")
            node.scope_distance = dist
            return var_type

        self._raise_exception(f"No variable named {node.text}", node)

    def _resolve_group(self, node: node.Node) -> types.Type:
        return self.resolve(node.get('expression'))

    def _resolve_unary_expression(self, node: node.Node) -> types.Type:
        right = self.resolve(node.get('right'))

        match node.get('operator').text:
            case '!':
                if right == types.bool_type:
                    return right

            case '-':
                if right in (types.int_type, types.bool_type):
                    return right

            case _:
                raise Exception("Invalid unary operator")

        self._raise_exception(f"Cannot apply operator {node.get('operator').text} on type {right}", node)

    def _resolve_binary_expression(self, node: node.Node) -> types.Type:
        left = self.resolve(node.get('left'))
        right = self.resolve(node.get('right'))

        if left == types.int_type and right == types.ratio_type:
            left = types.ratio_type
        if left == types.ratio_type and right == types.int_type:
            right = types.ratio_type

        match node.get('operator').text:
            case 'and' | 'or':
                return left.get_common_ancestor(right)

            case '==' | '!=':
                return types.bool_type

            case '>' | '>=' | '<' | '<=' | '-' | '*' | '/':
                if left == right and left in (types.int_type, types.ratio_type):
                    return left

            case '+':
                if left == right and left in (types.int_type, types.ratio_type, types.str_type):
                    return left

            case _:
                raise Exception("invalid binary operator")

        self._raise_exception(f"cannot apply operator {node.get('operator').text} on types {left} and {right}", node)

    def _resolve_variable_declaration(self, node: node.Node) -> types.Type:
        value_type = self.resolve(node.get('value'))

        if declared_type_node := node.get_or_none('type'):
            var_type = self._get_type(declared_type_node)
        else:
            var_type = value_type

        if not var_type.can_assign(value_type):
            self._raise_exception(f"Cannot assign {value_type} expression to a {var_type} variable", node)

        self._scope.declare(node.get('name').text, var_type)
        return var_type

    def _resolve_variable_assignment(self, node: node.Node) -> types.Type:
        if res := self._scope.get(node.get('name').text):
            var_type, dist = res

            value_type = self.resolve(node.get('value'))
            if not var_type.can_assign(value_type):
                self._raise_exception(f"cannot assign type {value_type} to a {var_type} variable", node)

            logger.debug(f"Resolved variable '{node.get('name').text}': {var_type=} and {dist=}")
            node.scope_distance = dist
            return var_type

        self._raise_exception(f"No variable named {node.get('name').text}", node)

    def _resolve_call(self, node: node.Node) -> types.Type:
        func_type = self.resolve(node.get('function'))
        if not isinstance(func_type, types.FunctionType):
            self._raise_exception("tried to call a non-function variable", node)

        argument_types = [self.resolve(arg) for arg in node.get_all('argument')]
        if not func_type.can_call(argument_types):
            self._raise_exception(f"Cannot call function type {func_type} with arguments {argument_types}", node)

        return func_type.return_type

    def _resolve_list(self, node: node.Node) -> types.Type:
        items_types = [self.resolve(item) for item in node.get_all('value')]
        if len(items_types) == 0:
            return types.ListType.get_or_create(element_type=types.any_type)

        if all([item_type == items_types[0] for item_type in items_types]):
            return types.ListType.get_or_create(items_types[0])

        self._raise_exception("non homogenous list", node)

    def _resolve_get_item(self, node: node.Node) -> types.Type:
        left = self.resolve(node.get('left'))
        if not isinstance(left, types.ListType):
            self._raise_exception("not a list", node)

        index = self.resolve(node.get('index'))
        if index != types.int_type:
            self._raise_exception("not a valid index", node)

        return left.element_type
