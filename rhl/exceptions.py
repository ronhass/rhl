class ErrorAtLocation(Exception):
    def __init__(self, message: str, lineno: int, column: int):
        super().__init__(message, lineno, column)
        self.message = message
        self.lineno = lineno
        self.column = column

    def __str__(self):
        return f"(line {self.lineno}, column {self.column}): {self.message}"


class RHLSyntaxError(ErrorAtLocation):
    def __str__(self):
        return f"Syntax error {super().__str__()}"


class RHLRuntimeError(ErrorAtLocation):
    def __str__(self):
        return f"Runtime error {super().__str__()}"


class RHLDivisionByZeroError(RHLRuntimeError):
    def __init__(self, lineno: int, column: int):
        super().__init__("division by zero encountered", lineno, column)
