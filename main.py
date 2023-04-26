import sys
import logging
import tree_sitter
from rhl.interpreter import Interpreter
from rhl.exceptions import RHLResolverError, RHLRuntimeError
from rhl.resolver import Resolver
from rhl.node import Node, State
import rhl.builtins

def setup_logging():
    logging.basicConfig(format='[%(levelname)s] %(name)s - %(message)s', level=logging.WARNING)


def get_ts_parser() -> tree_sitter.Parser:
    tree_sitter.Language.build_library('build/rhl.so', ['tree-sitter-rhl'])
    lang = tree_sitter.Language('build/rhl.so', 'rhl')
    parser = tree_sitter.Parser()
    parser.set_language(lang)
    return parser


def main():
    try:
        path = sys.argv[1]
    except IndexError:
        print(f"Usage: {sys.argv[0]} 'input_path'")
        return -1

    with open(path, "rb") as f:
        source = f.read()
        
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = get_ts_parser()
    tree = parser.parse(source)
    state = State()
    root = Node.get_or_create(tree.root_node, state)

    resolver = Resolver()
    try:
        resolver.visit(root)
    except RHLResolverError as ex:
        logger.error(ex)
        state.has_errors = True

    if state.has_errors:
        return -2

    interpreter = Interpreter()
    try:
        interpreter.execute(root)
    except RHLRuntimeError as ex:
        logger.error(ex)
        return -3


if __name__ == "__main__":
    main()
