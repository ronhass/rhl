import sys
from rhl.lexer import Lexer
from rhl.parser import Parser
from rhl.interpreter import Interpreter
from rhl.exceptions import RHLSyntaxError, RHLRuntimeError


def main():
    try:
        path = sys.argv[1]
    except IndexError:
        print(f"Usage: {sys.argv[0]} <input_path>")
        return -1

    with open(path) as f:
        source = f.read()

    lexer = Lexer(source)
    try:
        lexer.lex()
    except RHLSyntaxError as e:
        print(e)
        return -2

    parser = Parser(lexer.tokens)
    try:
        parser.parse()
    except RHLSyntaxError as e:
        print(e)
        return -3

    interpreter = Interpreter(parser.expressions)
    try:
        interpreter.interpret()
    except RHLRuntimeError as e:
        print(e)
        return -4


if __name__ == "__main__":
    main()
