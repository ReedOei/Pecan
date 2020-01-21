#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import ast

from functools import reduce

from pecan.lang.ast import *

@v_args(inline=True)
class PecanTransformer(Transformer):
    var_tok = str
    prop_val_tok = str
    escaped_str = lambda self, v: str(v[1:-1]) # Remove the quotes, which are the first and last characters
    varlist = lambda self, *vals: list(map(VarRef, list(vals)))
    args = lambda self, *args: list(args)

    def int_tok(self, const):
        if const.type != "INT":
            raise AutomatonArithmeticError("Constants need to be integers: " + const)
        return int(const.value)

    formals = lambda self, *args: list(args)

    praline_def = PralineDef
    praline_display = PralineDisplay
    praline_execute = PralineExecute

    def operator_sym(self, *syms):
        return PralineVar(''.join(str(sym) for sym in syms))

    def praline_operator(self, a, op, b):
        return PralineApp(PralineApp(op, a), b)

    def partial_op_fst(self, a, op):
        return PralineApp(op, a)

    def partial_op_snd(self, op, b):
        return PralineApp(PralineApp(PralineVar('flip'), op), b)

    praline_if = PralineIf
    praline_let_pecan = PralineLetPecan
    praline_let = PralineLet

    praline_tuple = lambda self, *args: PralineTuple(list(args))

    praline_var = PralineVar

    praline_add = lambda self, *args: reduce(PralineAdd, args)
    praline_sub = lambda self, *args: reduce(PralineSub, args)
    praline_div = lambda self, *args: reduce(PralineDiv, args)
    praline_mul = lambda self, *args: reduce(PralineMul, args)

    praline_neg = PralineNeg
    praline_app = PralineApp
    praline_compose = lambda self, f, g: PralineApp(PralineApp(PralineVar('compose'), f), g)
    praline_prepend = PralineList
    praline_exponent = lambda self, *args: reduce(PralineExponent, args)
    praline_match = lambda self, t, *arms: PralineMatch(t, list(arms))
    praline_match_arm = PralineMatchArm

    praline_match_int = PralineMatchInt

    praline_match_tuple = lambda self, *args: PralineMatchTuple(list(args))

    praline_match_string = PralineMatchString
    praline_match_var = PralineMatchVar
    praline_pecan_term = PralinePecanTerm

    praline_lambda = PralineLambda

    praline_int = PralineInt

    praline_string = PralineString

    praline_true = lambda self: PralineBool(True)
    praline_false = lambda self: PralineBool(False)

    praline_eq = PralineEq
    praline_ne = PralineNe
    praline_le = PralineLe
    praline_ge = PralineGe
    praline_lt = PralineLt
    praline_gt = PralineGt

    def praline_match_list(self, *args):
        res = PralineMatchList(None, None)

        for arg in args[::-1]:
            res = PralineMatchList(arg, res)

        return res

    praline_match_prepend = PralineMatchList

    praline_do = lambda self, *terms: PralineDo(list(terms))

    def praline_list_gen(self, start, end):
        return PralineApp(PralineApp(PralineVar('enumFromTo'), start), end)

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
    directive_save_aut = DirectiveSaveAut
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
        return NamedPred(pred_name, [VarRef(var_name)], body)

    def def_pred_is_call(self, var_name, pred_name, pred_args, body=None):
        return NamedPred(pred_name, [VarRef(var_name)] + pred_args, body)

    def var(self, letter, *args):
        return letter + ''.join(args)

    add = lambda self, *args: reduce(Add, args)
    sub = lambda self, *args: reduce(Sub, args)
    mul = lambda self, *args: reduce(Mul, args)
    div = lambda self, *args: reduce(Div, args)

    neg = Neg

    int_const = IntConst

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

    def var_ref(self, name):
        return VarRef(str(name))

    formula_true = FormulaTrue
    formula_false = FormulaFalse

    spot_formula = SpotFormula

from pecan.lang.lark.parser import Lark_StandAlone

pecan_parser = Lark_StandAlone(transformer=PecanTransformer())

