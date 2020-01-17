#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

from lark import Lark, Transformer, v_args

from pecan.lang.ast import *

pecan_grammar = """
?start: _NEWLINE* defs  -> prog

?defs:          -> nil_def
     | def -> single_def
     | def _NEWLINE+ defs -> multi_def

?def: pred_definition
    | restriction
    | "#" "save_aut" "(" string "," var ")" -> directive_save_aut
    | "#" "save_aut_img" "(" string "," var ")" -> directive_save_aut_img
    | "#" "context" "(" string "," string ")" -> directive_context
    | "#" "end_context" "(" string ")" -> directive_end_context
    | "#" "load" "(" string "," string "," formal ")" -> directive_load_aut
    | "#" "assert_prop" "(" PROP_VAL "," var ")" -> directive_assert_prop
    | "#" "import" "(" string ")" -> directive_import
    | "#" "forget" "(" var ")" -> directive_forget
    | "#" "type" "(" formal "," val_dict ")" -> directive_type
    | "#" "show_word" "(" var "," formal "," int "," int ")" -> directive_show_word
    | "#" "accepting_word" "(" var ")" -> directive_accepting_word
    | "#" "shuffle" "(" formal "," formal "," formal ")" -> directive_shuffle
    | "#" "shuffle_or" "(" formal "," formal "," formal ")" -> directive_shuffle_or
    | directive

?directive: "Definition" app ":=" _NEWLINE* term "." -> praline_def
          | "Execute" term "."             -> praline_execute
          | "Display" term "."             -> praline_display

?term: "if" term "then" term "else" term -> praline_if
     | praline_operator
     | "\\\\" app "->" term -> praline_lambda
     | "let" var "be" pecan_term "in" term -> praline_let_pecan
     | "let" var ":=" term "in" term -> praline_let
     | "match" term "with" _NEWLINE* (match_arm)+ _NEWLINE* "end" -> praline_match

?match_arm: "case" match_expr "=>" term _NEWLINE* -> praline_match_arm

?match_expr: int -> praline_match_int
    | string -> praline_match_string
    | var -> praline_match_var
    | "[" [ match_expr ("," match_expr)* ] "]" -> praline_match_list
    | match_expr "::" match_expr -> praline_match_prepend
    // | praline_tuple -> praline_match_tuple
    // TODO: Add praline_tuple back here...

?praline_operator: praline_sub

?praline_sub: praline_add ("-" _NEWLINE* praline_add)* -> praline_sub
?praline_add: praline_mul ("+" _NEWLINE* praline_mul)* -> praline_add
?praline_mul: praline_div ("*" _NEWLINE* praline_div)* -> praline_mul
?praline_div: praline_exponent ("/" _NEWLINE* praline_exponent)* -> praline_div

?praline_exponent: praline_prepend "^" praline_prepend -> praline_exponent
                 | praline_prepend

?praline_prepend: praline_compose "::" praline_compose -> praline_prepend
                | praline_compose

?praline_compose: app "∘" app -> praline_compose
                | app

?app: app praline_atom -> praline_app
    | praline_atom

?praline_atom: var -> var_ref
     | "-" praline_atom -> praline_neg
     | int
     | string
     | "(" term ")"
     | praline_list
     | praline_tuple
     | pecan_term

?pecan_term: "{" pred "}" -> praline_pecan_term

?praline_list: "[" [ term ("," term)* ] "]" -> praline_list_literal
             | "[" term "." "." ["."] term "]" -> praline_list_gen

?praline_tuple: "(" (term ",")+ [term] ")"

?val_dict: "{" [_NEWLINE* kv_pair _NEWLINE* ("," _NEWLINE* kv_pair _NEWLINE*)*] "}"
?kv_pair: string ":" var "(" args ")" -> kv_pair

?restriction: varlist ("are" | _IS) var -> restrict_is
            | varlist ("are" | _IS) var "(" varlist ")" -> restrict_call
varlist: var ("," var)*

_IS: "is" | "∈"

?pred_definition: var "(" formals ")" ":=" _NEWLINE* pred -> def_pred_standard
                | var _IS var [":=" _NEWLINE* pred] -> def_pred_is
                | var _IS var "(" formals ")" [":=" _NEWLINE* pred] -> def_pred_is_call

formals: [formal ("," formal)*]
formal: var -> formal_var
      | var "(" varlist ")" -> formal_call
      | var _IS var -> formal_is
      | var _IS var "(" varlist ")" -> formal_is_call

?pred: bool
     | pred _IMPLIES _NEWLINE* pred                -> implies
     | "if" pred "then" _NEWLINE* pred             -> implies
     | "if" pred "then" _NEWLINE* pred _ELSE _NEWLINE* pred -> if_then_else
     | bool _IFF _NEWLINE* pred                    -> iff
     | bool "if" "and" "only" "if" _NEWLINE* pred  -> iff
     | bool "iff" pred                   -> iff
     | bool _DISJ _NEWLINE* pred -> disj
     | bool _CONJ _NEWLINE* pred -> conj
     | forall_sym formal "." _NEWLINE* pred       -> forall
     | exists_sym formal "." _NEWLINE* pred       -> exists
     | _COMP pred -> comp

?bool: expr
     | "true"  -> formula_true
     | "false" -> formal_false
     | string                           -> spot_formula
     | "(" pred ")"
     | comparison

?comparison: expr _EQ expr                     -> equal
           | expr _NE expr                     -> not_equal
           | expr "<" expr                     -> less
           | expr ">" expr                     -> greater
           | expr _LE expr                     -> less_equal
           | expr _GE expr                     -> greater_equal

?expr: arith
     | var "[" arith "]"  -> index
     | var "[" arith "." "." ["."] arith "]" -> index_range

?arith: sub_expr

?sub_expr: add_expr ("-" _NEWLINE* add_expr)* -> sub
?add_expr: mul_expr ("+" _NEWLINE* mul_expr)* -> add
?mul_expr: div_expr ("*" _NEWLINE* div_expr)* -> mul
?div_expr: atom ("/" _NEWLINE* atom)* -> div

?atom: var -> var_ref
     | int
     | "-" atom  -> neg
     | "(" arith ")"
     | call

args: [arg ("," arg)*]
?arg: expr

call: var "(" args ")" -> call_args
     | atom _IS var     -> call_is
     | atom _IS var "(" args ")" -> call_is_args

int: INT -> const

var: VAR -> var_tok

?string: ESCAPED_STRING -> escaped_str

PROP_VAL: "sometimes"i | "true"i | "false"i // case insensitive

_NE: "!=" | "/=" | "≠"
_COMP: "!" | "~" | "¬" | "not"
_GE: ">=" | "≥"
_LE: "<=" | "≤"

_IMPLIES: "=>" | "⇒" | "⟹ " | "->"
_IFF: "<=>" | "⟺" | "⇔"

_ELSE: "else" | "otherwise"

_EQ: "=" | "=="

_CONJ: "&" | "/\\\\" | "∧" | "and"
_DISJ: "|" | "\\\\/" | "∨" | "or"

?forall_sym: "forall" | "∀"
?exists_sym: "exists" | "∃"

_NEWLINE: /\\n/

VAR: /(?!(if|then|else|otherwise|only|iff|is|are|forall|exists|not|or|and|sometimes|true|false)\\b)[a-zA-Z_][a-zA-Z_0-9]*/i

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
    escaped_str = lambda self, v: str(v[1:-1]) # Remove the quotes, which are the first and last characters
    varlist = lambda self, *vals: list(map(VarRef, list(vals)))
    args = lambda self, *args: list(args)
    formals = lambda self, *args: list(args)

    praline_def = PralineDef
    praline_display = PralineDisplay
    praline_execute = PralineExecute

    praline_if = PralineIf
    praline_let_pecan = PralineLetPecan
    praline_let = PralineLet

    praline_tuple = lambda self, *args: PralineTuple(args)

    praline_add = lambda self, *args: reduce(PralineAdd, args)
    praline_sub = lambda self, *args: reduce(PralineSub, args)
    praline_div = lambda self, *args: reduce(PralineDiv, args)
    praline_mul = lambda self, *args: reduce(PralineMul, args)

    praline_neg = PralineNeg
    praline_app = PralineApp
    praline_compose = PralineCompose
    praline_prepend = PralineList
    praline_exponent = PralineExponent
    praline_match = lambda self, t, *arms: PralineMatch(t, list(arms))
    praline_match_arm = PralineMatchArm

    praline_match_int = PralineMatchInt
    praline_match_string = PralineMatchString
    praline_match_var = PralineMatchVar
    praline_pecan_term = PralinePecanTerm

    praline_lambda = PralineLambda

    def praline_match_list(self, *args):
        res = PralineMatchList(None, None)

        for arg in args[::-1]:
            res = PralineMatchList(arg, res)

        return res

    praline_match_prepend = PralineMatchList

    def praline_list_gen(self, start, end):
        return PralineApp(PralineApp(VarRef('enumFromTo'), start), end)

    def praline_list_literal(self, *args):
        res = PralineList(None, None)

        for arg in args[::-1]:
            res = PralineList(arg, res)

        return res

    restrict_is = lambda self, varlist, var_ref: Restriction(varlist, Call(var_ref, []))
    restrict_call = lambda self, varlist, call_name, call_arg_vars: Restriction(varlist, Call(call_name, call_arg_vars))

    formal_is = lambda self, var_name, call_name: Call(call_name, [VarRef(var_name)])
    formal_is_call = lambda self, var_name, call_name, call_args: Call(call_name, [VarRef(var_name)] + call_args)
    formal_call = lambda self, call_name, call_args: Call(call_name, call_args)
    formal_var = VarRef

    call_args = Call
    call_is = lambda self, var_name, call_name: Call(call_name, [var_name])
    call_is_args = lambda self, var_name, call_name, args: Call(call_name, [var_name] + args)

    val_dict = lambda self, *pairs: dict(pairs)

    # TODO: Idealy we would allow all forms of calls here (e.g., "n is nat")
    kv_pair = lambda self, key, pred_name, args: (key, Call(pred_name, args))

    def restrict_many(self, args, pred):
        if type(pred) is VarRef: # If we do something like `x,y,z are nat`
            return Restriction(args, Call(pred.var_name, []))
        else:
            return Restriction(args, pred)

    directive_assert_prop = DirectiveAssertProp
    directive_type = DirectiveType
    directive_show_word = DirectiveShowWord
    directive_save_aut = DirectiveSaveAut
    directive_accepting_word = DirectiveAcceptingWord
    directive_save_aut_img = DirectiveSaveAutImage
    directive_context = DirectiveContext
    directive_end_context = DirectiveEndContext
    directive_load_aut = DirectiveLoadAut
    directive_import = DirectiveImport
    directive_forget = DirectiveForget

    def directive_shuffle(self, pred_a, pred_b, output_pred):
        return DirectiveShuffle(False, pred_a, pred_b, output_pred)

    def directive_shuffle_or(self, pred_a, pred_b, output_pred):
        return DirectiveShuffle(True, pred_a, pred_b, output_pred)

    prog = Program

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
            return self.restrict_is([VarRef(var_name)], pred_name)
        else:
            return NamedPred(pred_name, [VarRef(var_name)], body)

    def def_pred_is_call(self, var_name, pred_name, pred_args, body=None):
        if body is None:
            return self.restrict_call([VarRef(var_name)], pred_name, pred_args)
        else:
            return NamedPred(pred_name, [VarRef(var_name)] + pred_args, body)

    def var(self, letter, *args):
        return letter + ''.join(args)

    add = lambda self, *args: reduce(Add, args)
    sub = lambda self, *args: reduce(Sub, args)
    mul = lambda self, *args: reduce(Mul, args)
    div = lambda self, *args: reduce(Div, args)

    neg = Neg

    def const(self, const):
        if const.type != "INT":
            raise AutomatonArithmeticError("Constants need to be integers: " + const)
        const = int(const.value)
        return IntConst(const)

    index = Index
    index_range = IndexRange

    def equal(self, a, b):
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

    def not_equal(self, a, b):
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

    less = Less
    greater = Greater
    less_equal = LessEquals
    greater_equal = GreaterEquals

    def if_then_else(self, cond, p1, p2):
        return Conjunction(Implies(cond, p1), Implies(Complement(cond), p2))

    iff = Iff
    implies = Implies
    conj = Conjunction
    disj = Disjunction
    comp = Complement

    def forall(self, quant, var_name, pred):
        return Forall(var_name, pred)

    def exists(self, quant, var_name, pred):
        return Exists(var_name, pred)

    def var_ref(self, name):
        return VarRef(str(name))

    formula_true = FormulaTrue
    formula_false = FormulaFalse

    spot_formula = SpotFormula

pecan_parser = Lark(pecan_grammar, parser='lalr', transformer=PecanTransformer(), propagate_positions=True)
pred_parser = Lark(pecan_grammar, parser='lalr', transformer=PecanTransformer(), propagate_positions=True, start='pred')

