#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from colorama import Fore, Style

import time
import os
from functools import reduce

from lark import Lark, Transformer, v_args
import spot

from pecan.lang.ast.base import *

class VarRef(Expression):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name
        self.is_int = False

    def transform(self, transformer):
        return transformer.transform_VarRef(self)

    def show(self):
        return str(self.var_name)

class AutLiteral(Predicate):
    def __init__(self, aut):
        super().__init__()
        self.aut = aut
        self.is_int = False

    def transform(self, transformer):
        return transformer.transform_AutLiteral(self)

    def show(self):
        return repr(self)

    def show(self):
        return 'AUTOMATON LITERAL'

class SpotFormula(Predicate):
    def __init__(self, formula_str):
        super().__init__()
        self.formula_str = formula_str

    def transform(self, transformer):
        return transformer.transform_SpotFormula(self)

    def show(self):
        return 'LTL({})'.format(self.formula_str)

class OmegaRegularExpression(Predicate):
    def __init__(self, expr_str):
        super().__init__()
        self.expr_str = expr_str
        print(expr_str)

    def transform(self, transformer):
        return transformer.transform_OmegaRegularExpression(self)

    def show(self):
        return 'ω({})'.format(self.expr_str)

class Call(Predicate):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def transform(self, transformer):
        return transformer.transform_Call(self)

    def with_args(self, new_args):
        return Call(self.name, new_args)

    def add_arg(self, new_arg):
        return Call(self.name, self.args + [new_arg])

    def show(self):
        return '{}({})'.format(self.name, ', '.join(map(repr, self.args)))

class NamedPred(ASTNode):
    def __init__(self, name, args, body):
        super().__init__()
        self.name = name

        self.args = []
        self.arg_restrictions = {}
        for arg in args:
            if type(arg) is VarRef:
                self.args.append(arg)
            elif type(arg) is Call:
                var = arg.args[-1]
                self.args.append(var)
                self.arg_restrictions[var] = Restriction([var], arg.with_args(arg.args[:-1]))
            else:
                raise Exception("Argument '{}' is not: VarRef, or Call!".format(arg))

        self.body = body

    def transform(self, transformer):
        return transformer.transform_NamedPred(self)

    def show(self):
        return '{}({}) := {}'.format(self.name, ','.join(map(repr, self.args)), self.body)

class Program(ASTNode):
    def __init__(self, defs, *args, **kwargs):
        super().__init__()

        self.defs = defs
        self.preds = kwargs.get('preds', {})
        self.context = kwargs.get('context', {})
        self.restrictions = kwargs.get('restrictions', [{}])
        self.types = kwargs.get('types', {})
        self.eval_level = kwargs.get('eval_level', 0)
        self.result = kwargs.get('result', None)
        self.search_paths = kwargs.get('search_paths', [])

    def copy_defaults(self, other_prog):
        self.context = other_prog.context
        self.eval_level = other_prog.eval_level
        self.result = other_prog.result
        self.search_paths = other_prog.search_paths
        return self

    def extract_implications(self):
        from pecan.lang.ast.praline import PralineDirective
        from pecan.lang.ast.directives import DirectiveLoadAut

        restrict = {}
        for d in self.defs:
            if isinstance(d, PralineDirective):
                if d.name == 'Theorem':
                    a, b = self.extract_implication(restrict, d.term.vals[1].pecan_term)
                    safe_name = d.term.vals[0].val.replace(' ', '_').replace('.', '')

                    if a is not None and b is not None:
                        print(f'Implication ("{safe_name}", {{{a}}}, {{{b}}}).')
            elif isinstance(d, DirectiveLoadAut):
                print(d)
            elif isinstance(d, Restriction):
                for v in d.restrict_vars:
                    if v.var_name in restrict:
                        restrict[v.var_name].append(d.pred.add_arg(v))
                    else:
                        restrict[v.var_name] = [d.pred.add_arg(v)]

    def extract_implication(self, restrict, term):
        from pecan.lang.ast.quant import Forall
        from pecan.lang.ast.bool import Implies, Conjunction, BoolConst
        from pecan.lang.ast.annotation import Annotation
        if isinstance(term, Forall):
            cs = [ cond for cond in term.conds if cond is not None ]
            for v in term.vars:
                cs.extend(restrict.get(v.var_name, []))
            if len(cs) == 0:
                lhs = BoolConst(True)
            else:
                lhs = reduce(Conjunction, cs)
            l1, r1 = self.extract_implication(restrict, term.pred)
            if l1 is None:
                return lhs, r1
            else:
                return Conjunction(lhs, l1), r1
        elif isinstance(term, Implies):
            l1, r1 = self.extract_implication(restrict, term.b)
            if l1 is None:
                return term.a, r1
            else:
                return Conjunction(term.a, l1), r1
        elif isinstance(term, Annotation):
            return self.extract_implication(restrict, term.body)
        else:
            return None, term

    def transform(self, transformer):
        return transformer.transform_Program(self)

    def show(self):
        return repr(self.defs)

class Restriction(ASTNode):
    def __init__(self, restrict_vars, pred):
        super().__init__()
        self.restrict_vars = []
        for var in restrict_vars:
            if type(var) is VarRef:
                self.restrict_vars.append(var)
            else:
                raise Exception("Argument '{}' is not a valid var name (string or VarRef)".format(var_name))
        self.pred = pred

    def transform(self, transformer):
        return transformer.transform_Restriction(self)

    def show(self):
        return '{} are {}'.format(', '.join(map(repr, self.restrict_vars)), self.pred)

