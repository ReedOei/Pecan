# -*- coding=utf-8 -*-

from pecan.lang.pecan_ast import *

from lark import Lark, Transformer, v_args

pecan_grammar = """
    ?start: defs  -> prog

    ?defs:          -> nil_def
         | def -> single_def
         | def _NEWLINE+ defs -> multi_def

    ?def: pred_definition
        | restriction
        | "#" var -> directive
        | "#" "save_aut" "(" string "," var ")" -> directive_save_aut
        | "#" "save_aut_img" "(" string "," var ")" -> directive_save_aut_img
        | "#" "context" "(" string "," string ")" -> directive_context
        | "#" "end_context" "(" string ")" -> directive_end_context
        | "#" "load" "(" string "," string "," formal ")" -> directive_load
        | "#" "assert_prop" "(" PROP_VAL "," var ")" -> directive_assert_prop
        | "#" "import" "(" string ")" -> directive_import
        | "#" "forget" "(" var ")" -> directive_forget
        | "#" "type" "(" formal "," val_dict ")" -> directive_type
        | "#" "show_word" "(" var "," formal "," int "," int ")" -> directive_show_word

    ?val_dict: "{" [_NEWLINE* kv_pair _NEWLINE* ("," _NEWLINE* kv_pair _NEWLINE*)*] "}"
    ?kv_pair: string ":" call

    ?restriction: varlist ("are" | _IS) var -> restrict_is
                | varlist ("are" | _IS) var "(" varlist ")" -> restrict_call
    varlist: var ("," var)*

    _IS: "is" | "∈"

    ?pred_definition: var "(" formals ")" ":=" pred -> def_pred_standard
                    | var _IS var [":=" pred] -> def_pred_is
                    | var _IS var "(" formals ")" [":=" pred] -> def_pred_is_call

    formals: [formal ("," formal)*]
    ?formal: var
           | var "(" varlist ")" -> formal_call
           | var _IS var -> formal_is
           | var _IS var "(" varlist ")" -> formal_is_call

    args: [arg ("," arg)*]
    ?arg: expr

    ?call: var "(" args ")" -> call_args
         | var _IS var     -> call_is
         | var _IS var "(" args ")" -> call_is_args

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
         | forall_sym formal "." pred       -> forall
         | exists_sym formal "." pred       -> exists
         | call
         | "(" pred ")"
         | string                           -> spot_formula
         | "true"  -> formula_true
         | "false" -> formal_false

    ?expr: arith
         | var "[" arith "]"  -> index
         | var "[" arith "." "." ["."] arith "]" -> index_range

    ?arith: product
          | arith "+" product -> add
          | arith "+_" var product -> add_with_param
          | arith "-" product -> sub
          | arith "-_" var product -> sub_with_param

    ?product: atom
            | product "*" atom -> mul
            | product "*_" var atom -> mul_with_param
            | product "/" atom -> div
            | product "/_" var atom -> div_with_param

    ?atom: var -> var_ref
         | int
         | int "_" var -> const_with_param
         | "-" int  -> neg
         | "(" arith ")"

    int: INT -> const

    ?var: VAR -> var_tok

    ?string: ESCAPED_STRING -> escaped_str

    PROP_VAL: "sometimes"i | "true"i | "false"i // case insensitive

    NE: "!=" | "/=" | "≠"
    COMP: "!" | "~" | "¬" | "not"
    GE: ">=" | "≥"
    LE: "<=" | "≤"

    IMPLIES: "=>" | "⇒" | "⟹ " | "->"
    IFF: "<=>" | "⟺" | "⇔"

    EQ: "=" | "=="

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
    directive = Directive
    directive_assert_prop = DirectiveAssertProp
    directive_type = DirectiveType
    directive_show_word = DirectiveShowWord

    def formals(self, *args):
        return list(args)

    def restrict_is(self, varlist, var_ref):
        return Restriction(varlist, Call(var_ref, []))

    def restrict_call(self, varlist, call_name, call_arg_vars):
        return Restriction(varlist, Call(call_name, call_arg_vars))

    def formal_is(self, var_name, call_name):
        return Call(call_name, [var_name])

    def formal_is_call(self, var_name, call_name, call_args):
        return Call(call_name, [var_name] + call_args)

    def formal_call(self, call_name, call_args):
        return Call(call_name, call_args)

    def call_args(self, call_name, args):
        return Call(call_name, args)

    def call_is(self, var_name, call_name):
        return Call(call_name, [var_name])

    def call_is_args(self, var_name, call_name, args):
        return Call(call_name, [var_name] + args)

    def val_dict(self, *pairs):
        return dict(pairs)

    def kv_pair(self, key, val):
        key = key[1:-1]
        return (key, val)

    def restrict_many(self, args, pred):
        if type(pred) is VarRef: # If we do something like `x,y,z are nat`
            return Restriction(args, Call(pred.var_name, [])) # '' is a dummy value because it'll get replaced
        else:
            return Restriction(args, pred)

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

    def def_pred_standard(self, name, args, body):
        return NamedPred(name, args, body)

    # Unfortunately, Lark seems to have trouble determining when something is a predicate,
    # and when it is a restriction, so the body of predicates has been made optional.
    # If the body is not provided, then we just treat it as a restriction.
    # TODO: Fix?
    def def_pred_is(self, var_name, pred_name, body=None):
        if body is None:
            return self.restrict_is([var_name], pred_name)
        else:
            return NamedPred(pred_name, [var_name], body)

    def def_pred_is_call(self, var_name, pred_name, pred_args, body=None):
        if body is None:
            return self.restrict_call([var_name], pred_name, pred_args)
        else:
            return NamedPred(pred_name, [var_name] + pred_args, body)

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

    def index_range(self, var_name, start_expr, end_expr):
        return IndexRange(var_name, start_expr, end_expr)

    def equal(self, a, sym, b):
        # Resolve what sort of equality we're doing (e.g., "regular" equality, equality of subwords, etc.)

        # TODO: It would be nice to support automatic words with outputs other than 0 or 1
        if type(a) is Index and type(b) is IntConst:
            return EqualsCompareIndex(True, a, b)
        elif type(a) is IntConst and type(b) is Index:
            return EqualsCompareIndex(True, b, a)
        elif type(a) is Index and type(b) is Index:
            return EqualsCompareIndex(True, a, b)
        elif type(a) is IndexRange and type(b) is IndexRange:
            return EqualsCompareRange(True, a, b)
        else:
            return Equals(a, b)

    def not_equal(self, a, sym, b):
        # Resolve what sort of equality we're doing (e.g., "regular" equality, equality of subwords, etc.)
        if type(a) is Index and type(b) is IntConst:
            return EqualsCompareIndex(False, a, b)
        elif type(a) is IntConst and type(b) is Index:
            return EqualsCompareIndex(False, b, a)
        elif type(a) is Index and type(b) is Index:
            return EqualsCompareIndex(False, a, b)
        elif type(a) is IndexRange and type(b) is IndexRange:
            return EqualsCompareRange(False, a, b)
        else:
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

    def formula_true(self):
        return FormulaTrue()

    def formula_false(self):
        return FormulaFalse()

    def spot_formula(self, formula_str):
        return SpotFormula(formula_str[1:-1])

pecan_parser = Lark(pecan_grammar, parser='lalr', transformer=PecanTransformer(), propagate_positions=True)

