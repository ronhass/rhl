class SyntaxError(Exception):
    def __init__(self, message: str, lineno: int, column: int):
        super().__init__(message, lineno, column)

        self.message = message
        self.lineno = lineno
        self.column = column

    def __str__(self):
        return f"Syntax error (line {self.lineno}, column {self.column}): {self.message}"
