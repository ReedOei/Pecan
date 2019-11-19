# -*- coding=utf-8 -*-

from pecan.lang.pecan_ast import *

from lark import Lark, Transformer, v_args

pecan_grammar = """
    ?start: defs  -> prog

    ?defs:          -> nil_def
         | def -> single_def
         | def NEWLINES defs -> multi_def

    ?def: call DEFEQ pred       -> def_pred
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

    ?restriction: call  -> restrict_call
                | args_nonempty "are" pred_ref -> restrict_many

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

    ?args_nonempty: var -> single_arg
                  | var "," args       -> multi_arg

    ?args: -> nil_arg
         | args_nonempty

    ?expr: arith
         | var "[" arith "]"  -> index

    ?arith: product
          | arith "+" product -> add
          | arith "-" product -> sub

    ?product: atom
            | product MUL atom -> mul
            | product "/" atom -> div

    ?atom: var -> var_ref
         | INT      -> const
         | "-" INT  -> neg
         | "(" arith ")"

    ?var: VAR -> var_tok

    ?string: ESCAPED_STRING -> escaped_str

    MUL: "*" | "⋅"

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

    ?forall_sym: "A" | "forall" | "∀"
    ?exists_sym: "E" | "exists" | "∃"

    NEWLINE: /\\n/

    VAR: /(?!(forall|exists|not|or|and|sometimes|true|false)\\b)[a-zA-Z_][a-zA-Z_0-9]*/i

    COMMENT: "//" /(.)+/ NEWLINE

    %ignore COMMENT

    %import common.INT
    %import common.WS_INLINE
    %import common.ESCAPED_STRING

    %ignore WS_INLINE
    """

@v_args(inline=True)
class PecanTransformer(Transformer):
    def var_tok(self, tok):
        return str(tok)

    def restrict_call(self, call):
        if len(call.args) <= 0:
            raise Exception("Cannot restrict a call with no arguments: {}".format(call))

        return Restriction(call.args[0], call.replace_first)

    def restrict_many(self, args, pred):
        if type(pred) is VarRef:
            return Restriction(args, Call(pred.var_name, ['']).replace_first) # '' is a dummy value because it'll get replaced
        else:
            return Restriction(args, pred.replace_first)

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

    def directive_context(self, key, val):
        return DirectiveContext(key, val)

    def directive_end_context(self, context_name):
        return DirectiveEndContext(context_name)

    def directive_load(self, filename, aut_format, pred):
        return DirectiveLoadAut(filename, aut_format, pred)

    def directive_assert_prop(self, bool_val, pred_name):
        return DirectiveAssertProp(bool_val, pred_name)

    def directive_import(self, filename):
        return DirectiveImport(filename)

    def directive_forget(self, var_name):
        return DirectiveForget(var_name)

    def prog(self, defs):
        return Program(defs)

    def nil_def(self):
        return []

    def multi_def(self, d, newlines, ds):
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

    def mul(self, a, sym, b):
        return Mul(a, b)

    def div(self, a, b):
        return Div(a, b)

    def neg(self, a):
        return Neg(a)

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

    def nil_arg(self):
        return []

    def spot_formula(self, formula_str):
        return SpotFormula(formula_str[1:-1])

    def single_arg(self, arg):
        return [arg]

    def multi_arg(self, arg, args):
        return [arg] + args

pecan_parser = Lark(pecan_grammar, parser='lalr', transformer=PecanTransformer(), propagate_positions=True)

