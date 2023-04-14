import sys
import logging
from rhl.lexer import Lexer
from rhl.parser import Parser
from rhl.interpreter import Interpreter
from rhl.exceptions import RHLSyntaxError, RHLRuntimeError
from rhl.resolver import Resolver
from rhl.builtins import init_builtins


def setup_logging():
    logging.basicConfig(format='[%(levelname)s] %(name)s - %(message)s', level=logging.WARNING)


def main():
    setup_logging()

    try:
        path = sys.argv[1]
    except IndexError:
        print(f"Usage: {sys.argv[0]} <input_path>")
        return -1

    with open(path) as f:
        source = f.read()

    init_builtins()

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

    resolver = Resolver()
    resolver.resolve_statement(parser.root)

    interpreter = Interpreter()
    try:
        interpreter.execute(parser.root)
    except RHLRuntimeError as e:
        print(e)
        return -4


if __name__ == "__main__":
    main()
