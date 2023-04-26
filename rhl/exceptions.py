from . import node


class ErrorWithNode(Exception):
    def __init__(self, message: str, node: node.Node):
        super().__init__(message, node)
        self.message = message
        self.node = node

    def __str__(self):
        return f"{self.node.start_point} - {self.node.end_point}: {self.message}"


class RHLSyntaxError(ErrorWithNode):
    def __str__(self):
        return f"Syntax error {super().__str__()}"


class RHLResolverError(ErrorWithNode):
    def __str__(self):
        return f"Resolver error {super().__str__()}"


class RHLRuntimeError(ErrorWithNode):
    def __str__(self):
        return f"Runtime error {super().__str__()}"


class RHLDivisionByZeroError(RHLRuntimeError):
    def __init__(self, node: node.Node):
        super().__init__("division by zero encountered", node)
