# -*- coding=utf-8 -*-

from pecan.lang.ast import *

from lark import Lark, Transformer, v_args

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
    formal: var -> formal_var
          | var "(" varlist ")" -> formal_call
          | var _IS var -> formal_is
          | var _IS var "(" varlist ")" -> formal_is_call

    args: [arg ("," arg)*]
    ?arg: expr

    ?call: var "(" args ")" -> call_args
         | expr _IS var     -> call_is
         | expr _IS var "(" args ")" -> call_is_args

    ?pred: expr _EQ expr                     -> equal
         | expr _NE expr                     -> not_equal
         | expr "<" expr                     -> less
         | expr ">" expr                     -> greater
         | expr _LE expr                     -> less_equal
         | expr _GE expr                     -> greater_equal
         | pred _IFF pred                    -> iff
         | pred "if" "and" "only" "if" pred  -> iff
         | pred "iff" pred                   -> iff
         | pred _IMPLIES pred                -> implies
         | "if" pred "then" pred             -> implies
         | "if" pred "then" pred _ELSE pred -> if_then_else
         | pred _CONJ pred                   -> conj
         | pred _DISJ pred                   -> disj
         | _COMP pred                        -> comp
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
          | arith "-" product -> sub

    ?product: atom
            | product "*" atom -> mul
            | product "/" atom -> div

    ?atom: var -> var_ref
         | int
         | "-" int  -> neg
         | "(" arith ")"

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

    ?forall_sym: "A" | "forall" | "∀"
    ?exists_sym: "E" | "exists" | "∃"

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

    kv_pair = lambda self, key, val: (key, val)

    def restrict_many(self, args, pred):
        if type(pred) is VarRef: # If we do something like `x,y,z are nat`
            return Restriction(args, Call(pred.var_name, []))
        else:
            return Restriction(args, pred)

    directive_assert_prop = DirectiveAssertProp
    directive_type = DirectiveType
    directive_show_word = DirectiveShowWord
    directive_save_aut = DirectiveSaveAut
    directive_save_aut_img = DirectiveSaveAutImage
    directive_context = DirectiveContext
    directive_end_context = DirectiveEndContext
    directive_load_aut = DirectiveLoadAut
    directive_import = DirectiveImport
    directive_forget = DirectiveForget

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

    add = Add
    sub = Sub
    mul = Mul
    div = Div
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

