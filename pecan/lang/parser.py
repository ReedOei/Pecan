# -*- coding=utf-8 -*-

from lang.pecan_ast import *

from lark import Lark, Transformer, v_args

pecan_grammar = """
    ?start: defs  -> prog

    ?defs:          -> nil_def
         | def -> single_def
         | def NEWLINES defs -> multi_def

    ?def: var "(" args ")" DEFEQ pred       -> def_pred
        | pred
        | "#" var -> directive
        | "#" "save_aut" "(" string "," var ")" -> directive_save_aut
        | "#" "save_aut_img" "(" string "," var ")" -> directive_save_aut_img
        | "#" "save_pred" "(" string "," var ")" -> directive_save_pred
        | "#" "context" "(" string ")" -> directive_context
        | "#" "end_context" "(" string ")" -> directive_end_context
        | "#" "load_preds" "(" string ")" -> directive_load_preds
        | "#" "load" "(" string "," string "," var "(" args ")" ")" -> directive_load
        | "#" "assert_prop" "(" PROP_VAL "," var ")" -> directive_assert_prop

    ?pred: expr EQ expr                    -> equal
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
         | string                           -> spot_formula

    ?args: -> nil_arg
         | var -> single_arg
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
         | INT      -> const
         | "-" INT  -> neg
         | "(" arith ")"

    ?var: LETTER ALPHANUM*

    ?string: ESCAPED_STRING -> escaped_str

    PROP_VAL: "sometimes"i | "true"i | "false"i // case insensitive

    NEWLINES: NEWLINE+

    DEFEQ: ":="

    NE: "!=" | "/=" | "≠"
    COMP: "!" | "~" | "¬" | "not"
    GE: ">=" | "≥"
    LE: "<=" | "≤"

    IMPLIES: "=>" | "⇒" | "⟹ " | "->"
    IFF: "<=>" | "⟺" | "⇔"

    EQ: "="

    CONJ: "&" | "/\\\\" | "∧" | "and"
    DISJ: "|" | "\\\\/" | "∨" | "or"

    FORALL: "A" | "forall" | "∀"
    EXISTS: "E" | "exists" | "∃"

    ALPHANUM: LETTER | "_" | DIGIT
    DIGIT: "0" .. "9"
    LETTER: UPPER_LETTER | LOWER_LETTER
    UPPER_LETTER: "A" .. "Z"
    LOWER_LETTER: "a" .. "z"

    NEWLINE: /\\n/

    %import common.INT
    %import common.WS_INLINE
    %import common.ESCAPED_STRING

    %ignore WS_INLINE
    """

@v_args(inline=True)
class PecanTransformer(Transformer):
    def escaped_str(self, str_tok):
        return str(str_tok)

    def directive(self, name):
        return Directive(name)

    def directive_save_aut(self, filename, pred_name):
        return DirectiveSaveAut(filename, pred_name)

    def directive_save_aut_img(self, filename, pred_name):
        return DirectiveSaveAutImage(filename, pred_name)

    def directive_save_pred(self, filename, pred_name):
        return DirectiveSavePred(filename, pred_name)

    def directive_context(self, context_name):
        return DirectiveContext(context_name)

    def directive_end_context(self, context_name):
        return DirectiveEndContext(context_name)

    def directive_load_preds(self, filename):
        return DirectiveLoadPreds(filename)

    def directive_load(self, filename, aut_format, pred_name, pred_args):
        return DirectiveLoadAut(filename, aut_format, pred_name, pred_args)

    def directive_assert_prop(self, bool_val, pred_name):
        return DirectiveAssertProp(bool_val, pred_name)

    def prog(self, defs):
        return Program(defs)

    def nil_def(self):
        return []

    def multi_def(self, d, newlines, ds):
        return [d] + ds

    def single_def(self, d):
        return [d]

    def def_pred(self, name, args, defeq, body):
        return NamedPred(name, args, body)

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
        if const.type != "INT":
            raise AutomatonArithmeticError("Constants need to be integers: " + const)
        const = int(const.value)
        return IntConst(const)

    def index(self, var_name, index_expr):
        return Index(var_name, index_expr)

    def equal(self, a, sym, b):
        return Equals(a, b)

    def not_equal(self, a, sym, b):
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

    def spot_formula(self, formula_str):
        return SpotFormula(formula_str[1:-1])

    def single_arg(self, arg):
        return [arg]

    def multi_arg(self, arg, args):
        return [arg] + args

pecan_parser = Lark(pecan_grammar, parser='lalr', transformer=PecanTransformer(), propagate_positions=True)

