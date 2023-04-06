from dataclasses import dataclass


@dataclass
class Token:
    line: int
    column: int

    def __str__(self):
        return self.__class__.__name__


@dataclass
class OneCharToken(Token):
    _CHAR: str


@dataclass
class LParenToken(OneCharToken):
    _CHAR: str = "("


@dataclass
class RParenToken(OneCharToken):
    _CHAR: str = ")"


@dataclass
class LBraceToken(OneCharToken):
    _CHAR: str = "{"


@dataclass
class RBraceToken(OneCharToken):
    _CHAR: str = "}"


@dataclass
class CommaToken(OneCharToken):
    _CHAR: str = ","


@dataclass
class DotToken(OneCharToken):
    _CHAR: str = "."


@dataclass
class ColonToken(OneCharToken):
    _CHAR: str = ":"


@dataclass
class SemiColonToken(OneCharToken):
    _CHAR: str = ";"


@dataclass
class PlusToken(OneCharToken):
    _CHAR: str = "+"


@dataclass
class MinusToken(OneCharToken):
    _CHAR: str = "-"


@dataclass
class StarToken(OneCharToken):
    _CHAR: str = "*"


@dataclass
class SlashToken(OneCharToken):
    _CHAR: str = "/"


@dataclass
class BangToken(OneCharToken):
    _CHAR: str = "!"


@dataclass
class EqualToken(OneCharToken):
    _CHAR: str = "="


@dataclass
class GreaterToken(OneCharToken):
    _CHAR: str = ">"


@dataclass
class LessToken(OneCharToken):
    _CHAR: str = "<"


@dataclass
class TwoCharsToken(Token):
    _CHARS: str


@dataclass
class BangEqualToken(TwoCharsToken):
    _CHARS: str = "!="


@dataclass
class EqualEqualToken(TwoCharsToken):
    _CHARS: str = "=="


@dataclass
class GreaterEqualToken(TwoCharsToken):
    _CHARS: str = ">="


@dataclass
class LessEqualToken(TwoCharsToken):
    _CHARS: str = "<="


@dataclass
class ReturnTypeToken(TwoCharsToken):
    _CHARS: str = "->"


@dataclass
class LiteralToken(Token):
    pass


@dataclass
class IdentifierToken(Token):
    name: str


@dataclass
class StringToken(Token):
    value: str


@dataclass
class IntegerToken(Token):
    value: int


@dataclass
class RationalToken(Token):
    value: float


@dataclass
class KeywordToken(Token):
    _KEY: str


@dataclass
class AndToken(KeywordToken):
    _KEY: str = "and"


@dataclass
class OrToken(KeywordToken):
    _KEY: str = "or"


@dataclass
class IfToken(KeywordToken):
    _KEY: str = "if"


@dataclass
class ElseToken(KeywordToken):
    _KEY: str = "else"


@dataclass
class TrueToken(KeywordToken):
    _KEY: str = "true"


@dataclass
class FalseToken(KeywordToken):
    _KEY: str = "false"


@dataclass
class WhileToken(KeywordToken):
    _KEY: str = "while"


@dataclass
class FunctionToken(KeywordToken):
    _KEY: str = "fun"


@dataclass
class ClassToken(KeywordToken):
    _KEY: str = "class"


@dataclass
class NoneToken(KeywordToken):
    _KEY: str = "none"


@dataclass
class ReturnToken(KeywordToken):
    _KEY: str = "return"


@dataclass
class SuperToken(KeywordToken):
    _KEY: str = "super"


@dataclass
class ThisToken(KeywordToken):
    _KEY: str = "this"


@dataclass
class IntTypeToken(KeywordToken):
    _KEY: str = "int"


@dataclass
class FloatTypeToken(KeywordToken):
    _KEY: str = "float"


@dataclass
class BoolTypeToken(KeywordToken):
    _KEY: str = "bool"


@dataclass
class StringTypeToken(KeywordToken):
    _KEY: str = "str"


@dataclass
class EOFToken(Token):
    pass
