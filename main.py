import sys
from rhl.lexer import Lexer
from rhl.exceptions import SyntaxError


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
    except SyntaxError as e:
        print(e)
        return -2

    print(lexer.tokens)


if __name__ == "__main__":
    main()
