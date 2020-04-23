#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import ast

from functools import reduce

from lark import Lark, Transformer, v_args

from pecan.lang.ast import *

@v_args(inline=True)
class PecanTransformer(Transformer):
    var_tok = str
    prop_val_tok = str
    escaped_str = lambda self, v: str(v[1:-1]).replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t') # Remove the quotes, which are the first and last characters

    def varlist(self, *vals):
        return [VarRef(v) for v in vals]

    def args(self, *args):
        return list(args)

    def int_tok(self, const):
        if const.type != "INT":
            raise AutomatonArithmeticError("Constants need to be integers: " + const)
        return int(const.value)

    def praline_def(self, t, body):
        return PralineDef(t, body)

    def directive_name(self, name_tok):
        return str(name_tok)

    def praline_alias(self, name, _sym1, _sym2, _sym3, directive_name, term):
        return PralineAlias(name, directive_name, term)

    def praline_directive(self, name, term):
        return PralineDirective(name, term)

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

    def praline_let(self, match_pat, expr, body):
        if isinstance(match_pat, PralineMatchVar):
            return PralineLet(match_pat.var, expr, body)
        else:
            return PralineMatch(expr, [PralineMatchArm(match_pat, body)])

    def praline_tuple(self, *args):
        return PralineTuple(list(args))

    praline_var = PralineVar

    def praline_add(self, *args):
        return reduce(PralineAdd, args)

    def praline_sub(self, *args):
        return reduce(PralineSub, args)

    def praline_div(self, *args):
        return reduce(PralineDiv, args)

    def praline_mul(self, *args):
        return reduce(PralineMul, args)

    praline_neg = PralineNeg
    praline_app = PralineApp

    def praline_exponent(self, *args):
        return reduce(PralineExponent, args)

    def praline_match(self, t, *arms):
        return PralineMatch(t, list(arms))

    praline_match_arm = PralineMatchArm

    praline_match_int = PralineMatchInt

    def praline_match_tuple(self, *args):
        return PralineMatchTuple(list(args))

    def praline_match_pecan(self, pecan_term):
        return PralineMatchPecan(pecan_term)

    praline_match_string = PralineMatchString
    praline_match_var = PralineMatchVar
    praline_pecan_term = PralinePecanTerm

    praline_lambda = PralineLambda

    praline_int = PralineInt

    praline_string = PralineString

    def praline_true(self):
        return PralineBool(True)

    def praline_false(self):
        return PralineBool(False)

    def praline_match_list(self, *args):
        res = PralineMatchList(None, None)

        for arg in args[::-1]:
            res = PralineMatchList(arg, res)

        return res

    def praline_match_prepend(self, head, sym1, sym2, tail):
        return PralineMatchList(head, tail)

    def praline_do(self, *terms):
        return PralineDo(list(terms))

    def praline_list_gen(self, start, end):
        return PralineApp(PralineApp(PralineVar('enumFromTo'), start), end)

    def praline_list_literal(self, *args):
        res = PralineList(None, None)

        for arg in args[::-1]:
            res = PralineList(arg, res)

        return res

    def restrict_is(self, varlist, var_ref):
        return Restriction(varlist, Call(var_ref, []))

    def restrict_call(self, varlist, call_name, call_arg_vars):
        return Restriction(varlist, Call(call_name, call_arg_vars))

    def formal_is(self, var_name, call_name):
        return Call(call_name, [VarRef(var_name)])

    def formal_is_call(self, var_name, call_name, call_args):
        return Call(call_name, call_args + [VarRef(var_name)])

    def formal_call(self, call_name, call_args):
        return Call(call_name, call_args)

    def formal_var(self, var_name):
        return VarRef(var_name)

    def quant_formal_is(self, var_refs, call_name):
        return [Call(call_name, [v]) for v in var_refs]

    def quant_formal_is_call(self, var_refs, call_name, call_args):
        return [Call(call_name, call_args + [v]) for v in var_refs]

    def quant_formal_list(self, var_list):
        return var_list

    def call_args(self, name, args):
        return Call(name, args)

    def call_is(self, var_name, call_name):
        return Call(call_name, [var_name])

    def call_is_args(self, var_name, call_name, args):
        return Call(call_name, args + [var_name])

    def val_dict(self, *pairs):
        return dict(pairs)

    def kv_pair(self, key, sym, pred_name, args):
        return (key, Call(pred_name, args))

    def restrict_many(self, args, pred):
        if type(pred) is VarRef: # If we do something like `x,y,z are nat`
            return Restriction(args, Call(pred.var_name, []))
        else:
            return Restriction(args, pred)

    directive_assert_prop = DirectiveAssertProp

    def directive_structure(self, pred_ref, val_dict):
        return DirectiveStructure(pred_ref, val_dict)

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

    prog = lambda self, *defs: Program(list(defs))

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
        return NamedPred(pred_name, pred_args + [VarRef(var_name)], body)

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

    def less(self, a, sym, b):
        return Less(a, b)

    def greater(self, a, sym, b):
        return Greater(a, b)

    def less_equal(self, a, sym, b):
        return LessEquals(a, b)

    def greater_equal(self, a, sym, b):
        return GreaterEquals(a, b)

    def if_then_else(self, cond, p1, p2=None):
        if p2 is None:
            return Implies(cond, p1)
        else:
            return Conjunction(Implies(cond, p1), Implies(Complement(cond), p2))

    # These functions exist because the two forms of ge and le have different numbers of symbols; these standardize it
    def elim_ge(self, *args):
        return '>='

    def elim_le(self, *args):
        return '<='

    def elim_ne(self, *args):
        return '!='

    iff = Iff
    implies = Implies

    def conj(self, a, sym, b):
        return Conjunction(a, b)

    def disj(self, a, sym, b):
        return Disjunction(a, b)

    def comp(self, sym, a):
        return Complement(a)

    def forall(self, quant, var_preds, pred):
        return Forall(var_preds, pred)

    def exists(self, quant, var_preds, pred):
        return Exists(var_preds, pred)

    def var_ref(self, name):
        return VarRef(str(name))

    def formula_true(self):
        return BoolConst(True)

    def formula_false(self):
        return BoolConst(False)

    def spot_formula(self, formula_str):
        return SpotFormula(formula_str)

    def annotation(self, annotation_tok, pred):
        return Annotation(str(annotation_tok), pred)

from pecan.lang.lark.parser import Lark_StandAlone

# pecan_parser = Lark.open('pecan/lang/lark/pecan_grammar.lark', transformer=PecanTransformer(), parser='lalr')
pecan_parser = Lark_StandAlone(transformer=PecanTransformer())

