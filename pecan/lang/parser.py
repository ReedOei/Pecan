# -*- coding=utf-8 -*-

from pecan.lang.pecan_ast import *

from lark import Lark, Transformer, v_args

pecan_grammar = """
    ?start: defs  -> prog

    ?defs:          -> nil_def
         | def -> single_def
         | def _NEWLINE+ defs -> multi_def

    ?def: call DEFEQ pred       -> def_pred
        | call -> restrict_call
        | restriction
        | "#" var -> directive
        | "#" "save_aut" "(" string "," var ")" -> directive_save_aut
        | "#" "save_aut_img" "(" string "," var ")" -> directive_save_aut_img
        | "#" "save_pred" "(" string "," var ")" -> directive_save_pred
        | "#" "context" "(" string "," string ")" -> directive_context
        | "#" "end_context" "(" string ")" -> directive_end_context
        | "#" "load" "(" string "," string "," call ")" -> directive_load
        | "#" "assert_prop" "(" PROP_VAL "," var ")" -> directive_assert_prop
        | "#" "import" "(" string ")" -> directive_import
        | "#" "forget" "(" var ")" -> directive_forget
        | "#" "type" "(" pred_ref "," val_dict ")" -> directive_type

    ?val_dict: "{" [_NEWLINE* kv_pair _NEWLINE* ("," _NEWLINE* kv_pair _NEWLINE*)*] "}"
    ?kv_pair: string ":" pred_ref

    ?restriction: varlist "are" pred_ref -> restrict_many
    ?varlist: [var ("," var)*]

    ?args: [args_nonempty]
    ?args_nonempty: pred_ref ("," pred_ref)*

    ?pred_ref: var -> var_ref
             | call

    ?call: var "(" args ")" -> call_args
         | var "is" pred_ref     -> call_is

    ?pred: expr EQ expr                     -> equal
         | expr NE expr                     -> not_equal
         | expr "<" expr                    -> less
         | expr ">" expr                    -> greater
         | expr LE expr                     -> less_equal
         | expr GE expr                     -> greater_equal
         | pred IFF pred                    -> iff
         | pred IMPLIES pred                -> implies
         | pred CONJ pred                   -> conj
         | pred DISJ pred                   -> disj
         | COMP pred                        -> comp
         | forall_sym pred_ref "." pred              -> forall
         | exists_sym pred_ref "." pred              -> exists
         | call
         | "(" pred ")"
         | string                           -> spot_formula
         | "true"  -> formula_true
         | "false" -> formal_false

    ?expr: arith
         | var "[" arith "]"  -> index

    ?arith: product
          | arith "+" product -> add
          | arith "+_" var product -> add_with_param
          | arith "-" product -> sub
          | arith "-_" product -> sub_with_param

    ?product: atom
            | product "*" atom -> mul
            | product "*_" atom -> mul_with_param
            | product "/" atom -> div
            | product "/_" atom -> div_with_param

    ?atom: var -> var_ref
         | INT -> const
         | INT "_" var -> const_with_param
         | "-" INT  -> neg
         | "(" arith ")"

    ?var: VAR -> var_tok

    ?string: ESCAPED_STRING -> escaped_str

    PROP_VAL: "sometimes"i | "true"i | "false"i // case insensitive

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

    ?forall_sym: "A" | "forall" | "∀"
    ?exists_sym: "E" | "exists" | "∃"

    _NEWLINE: /\\n/

    VAR: /(?!(is|are|forall|exists|not|or|and|sometimes|true|false)\\b)[a-zA-Z_][a-zA-Z_0-9]*/i

    COMMENT: "//" /(.)+/ _NEWLINE

    %ignore COMMENT

    %import common.INT
    %import common.WS_INLINE
    %import common.ESCAPED_STRING

    %ignore WS_INLINE
    """

@v_args(inline=True)
class PecanTransformer(Transformer):
    var_tok = str
    escaped_str = str
    varlist = lambda self, *vals: list(vals)
    args = lambda self, *args: list(args)
    args_nonempty = lambda self, *args: list(args)
    directive = Directive
    directive_assert_prop = DirectiveAssertProp
    directive_type = DirectiveType

    def val_dict(self, *pairs):
        return dict(pairs)

    def kv_pair(self, key, val):
        key = key[1:-1]
        return (key, val)

    def restrict_call(self, call):
        if len(call.args) <= 0:
            raise Exception("Cannot restrict a call with no arguments: {}".format(call))

        return Restriction(call.args[0], Call(call.name, call.args[1:]).insert_first)

    def restrict_many(self, args, pred):
        if type(pred) is VarRef: # If we do something like `x,y,z are nat`
            return Restriction(args, Call(pred.var_name, []).insert_first) # '' is a dummy value because it'll get replaced
        else:
            return Restriction(args, pred.insert_first)

    def directive_save_aut(self, filename, pred_name):
        return DirectiveSaveAut(filename, pred_name)

    def directive_save_aut_img(self, filename, pred_name):
        return DirectiveSaveAutImage(filename, pred_name)

    def directive_save_pred(self, filename, pred_name):
        return DirectiveSavePred(filename, pred_name)

    def directive_context(self, key, val):
        return DirectiveContext(key, val)

    def directive_end_context(self, context_name):
        return DirectiveEndContext(context_name)

    def directive_load(self, filename, aut_format, pred):
        return DirectiveLoadAut(filename, aut_format, pred)

    def directive_import(self, filename):
        return DirectiveImport(filename)

    def directive_forget(self, var_name):
        return DirectiveForget(var_name)

    def prog(self, defs):
        return Program(defs)

    def nil_def(self):
        return []

    def multi_def(self, d, ds):
        return [d] + ds

    def single_def(self, d):
        return [d]

    def def_pred(self, pred, defeq, body):
        if type(pred) is Call:
            return NamedPred(pred.name, pred.args, body)
        elif type(pred) is VarRef:
            return NamedPred(pred.name, [], body)
        else:
            raise Exception('Invalid syntax in definition: {} := {}'.format(pred, body))

    def var(self, letter, *args):
        return letter + ''.join(args)

    def add(self, a, b):
        return Add(a, b)

    def sub(self, a, b):
        return Sub(a, b)

    def mul(self, a, b):
        return Mul(a, b)

    def div(self, a, b):
        return Div(a, b)

    def add_with_param(self, a, var, b):
        return Add(a, b, param=var)

    def sub_with_param(self, a, var, b):
        return Sub(a, b, param=var)

    def mul_with_param(self, a, var, b):
        return Mul(a, b, param=var)

    def div_with_param(self, a, var, b):
        return Div(a, b, param=var)

    def neg(self, a):
        return Neg(a)

    def const(self, const):
        if const.type != "INT":
            raise AutomatonArithmeticError("Constants need to be integers: " + const)
        const = int(const.value)
        return IntConst(const)

    def const_with_param(self, const, var):
        if const.type != "INT":
            raise AutomatonArithmeticError("Constants need to be integers: " + const)
        const = int(const.value)
        return IntConst(const, param=var)

    def index(self, var_name, index_expr):
        return Index(var_name, index_expr)

    def equal(self, a, sym, b):
        return Equals(a, b)

    def not_equal(self, a, sym, b):
        return NotEquals(a, b)

    def less(self, a, b):
        return Less(a, b)

    def greater(self, a, b):
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

    def call_args(self, name, args):
        return Call(name, args)

    def var_ref(self, name):
        return VarRef(str(name))

    def call_is(self, name, pred_other):
        if type(pred_other) is Call:
            return Call(pred_other.name, [name] + pred_other.args)
        elif type(pred_other) is VarRef:
            return Call(pred_other.var_name, [name])
        else:
            raise Exception('Unexpected value after `is`: {}'.format(pred_other))

    def formula_true(self):
        return FormulaTrue()

    def formula_false(self):
        return FormulaFalse()

    def spot_formula(self, formula_str):
        return SpotFormula(formula_str[1:-1])

pecan_parser = Lark(pecan_grammar, parser='lalr', transformer=PecanTransformer(), propagate_positions=True)

