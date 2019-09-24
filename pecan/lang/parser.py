# -*- coding=utf-8 -*-

from pecan.lang.pecan_ast import *

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
            | product MUL atom -> mul
            | product "/" atom -> div

    MUL: "*" | "⋅"

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
    def var(self, letter, *args):
        return letter + ''.join(args)

    def add(self, a, b):
        return Add(a, b)

    def sub(self, a, b):
        return Sub(a, b)

    def mul(self, a, sym, b):
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

    def greater(self, a, sym, b):
        return Greater(a, b)

    def less_equal(self, a, sym, b):
        return LessEquals(a, b)

    def greater_equal(self, a, sym, b):
        return GreaterEquals(a, b)

    def iff(self, a, sym, b):
        return Iff(a, b)

    def iff_words(self, a, b):
        return Iff(a, b)

    def implies(self, a, sym, b):
        return Implies(a, b)

    def implies_words(self, a, sym, b):
        return Implies(a, b)

    def conj(self, a, sym, b):
        return Conjunction(a, b)

    def disj(self, a, sym, b):
        return Disjunction(a, b)

    def comp(self, sym, a):
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

