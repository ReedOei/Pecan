from pecan_ast import *

from lark import Lark, Transformer, v_args

pecan_grammar = """
    ?start: pred

    ?pred: expr "=" expr                    -> equal
         | expr NE expr                     -> not_equal
         | expr "<" expr                    -> less
         | expr ">" expr                    -> greater
         | expr LE expr                     -> less_equal
         | expr GE expr                     -> greater_equal
         | pred IFF pred                    -> iff
         | pred "if" "and" "only" "if" pred -> iff_words
         | pred IMPLIES pred                -> implies
         | pred "if" pred                   -> back_implies_words
         | pred BACK_IMPLIES pred           -> back_implies
         | "if" pred "then" pred            -> implies_words
         | pred CONJ pred                   -> conj
         | pred DISJ pred                   -> disj
         | COMP pred                        -> comp
         | FORALL var "." pred                  -> forall
         | EXISTS var "." pred                  -> exists
         | var "(" args ")"                 -> call
         | "(" pred ")"

    ?args: -> nil_arg
         | var "," args       -> multi_arg

    ?expr: arith
         | var "[" arith "]"  -> index

    ?arith: product
          | arith "+" product -> add
          | arith "-" product -> sub

    ?product: atom
            | product mul atom -> mul
            | product "/" atom -> div

    ?mul: "*" | "⋅"

    ?atom: var         -> var_ref
         | NUMBER      -> const
         | "-" NUMBER  -> neg
         | "(" arith ")"

    ?var: LETTER ALPHANUM*

    COMP: "~" | "¬" | "not"
    NE: "!=" | "/=" | "≠"
    GE: ">=" | "≥"
    LE: "<=" | "≤"

    IMPLIES: "=>" | "⇒" | "⟹ "
    BACK_IMPLIES: "<=" | "⇐" | "⟸"
    IFF: "<=>" | "⟺" | "⇔"

    CONJ: "&" | "/\\\\" | "∧" | "and"
    DISJ: "|" | "\\\\/" | "∨" | "or"

    FORALL: "A" | "forall" | "∀"
    EXISTS: "E" | "exists" | "∃"

    ALPHANUM: LETTER | "_" | DIGIT
    DIGIT: "0" .. "9"
    LETTER: UPPER_LETTER | LOWER_LETTER
    UPPER_LETTER: "A" .. "Z"
    LOWER_LETTER: "a" .. "z"

    %import common.NUMBER
    %import common.WS_INLINE

    %ignore WS_INLINE
    """

@v_args(inline=True)
class PecanTransformer(Transformer):
    def __init__(self):
        pass

    def add(self, a, b):
        return Add(a, b)

    def sub(self, a, b):
        return Sub(a, b)

    def mul(self, a, b):
        return Mul(a, b)

    def div(self, a, b):
        return Div(a, b)

    def neg(self, a):
        return Neg(a)

    def var_ref(self, var_name):
        return VarRef(var_name)

    def const(self, const):
        return IntConst(const)

    def index(self, var_name, index_expr):
        return Index(var_name, index_expr)

    def equal(self, a, b):
        return Equals(a, b)

    def not_equal(self, a, b):
        return NotEquals(a, b)

    def less(self, a, b):
        return Less(a, b)

    def greater(self, a, b):
        return Greater(a, b)

    def less_equal(self, a, b):
        return LessEquals(a, b)

    def greater_equal(self, a, b):
        return GreaterEquals(a, b)

    def iff(self, a, b):
        return Iff(a, b)

    def iff_words(self, a, b):
        return Iff(a, b)

    def implies(self, a, b):
        return Implies(a, b)

    # We directly convert the back_implies into regular implies
    def back_implies(self, a, b):
        return Implies(b, a)

    def back_implies_words(self, a, b):
        return Implies(b, a)

    def implies_words(self, a, b):
        return Implies(a, b)

    def conj(self, a, b):
        return Conjunction(a, b)

    def disj(self, a, b):
        return Disjunction(a, b)

    def comp(self, a):
        return Complement(a)

    def forall(self, quant, var_name, pred):
        return Forall(var_name, pred)

    def exists(self, quant, var_name, pred):
        return Exists(var_name, pred)

    def call(self, name, args):
        return Call(name, args)

    def nil_arg(self):
        return []

    def mul_arg(self, arg, args):
        return [arg] + args

pecan_parser = Lark(pecan_grammar, parser='lalr', transformer=PecanTransformer(), propagate_positions=True)
print(pecan_parser.parse('forall x.x=x'))
print(pecan_parser.parse('forall x.if 1 = C[x + y] then (a = b if (exists z. a + b = z))'))

