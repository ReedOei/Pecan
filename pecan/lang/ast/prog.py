#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from colorama import Fore, Style

import time
import os
from functools import reduce

from lark import Lark, Transformer, v_args
import spot

from pecan.tools.automaton_tools import AutomatonTransformer, Substitution
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

    def __repr__(self):
        return 'AUTOMATON LITERAL' # TODO: Maybe improve this?

class SpotFormula(Predicate):
    def __init__(self, formula_str):
        super().__init__()
        self.formula_str = formula_str

    def transform(self, transformer):
        return transformer.transform_SpotFormula(self)

    def __repr__(self):
        return 'LTL({})'.format(self.formula_str)

class Call(Predicate):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def transform(self, transformer):
        return transformer.transform_Call(self)

    def insert_first(self, new_arg):
        return Call(self.name, [new_arg] + self.args)

    def __repr__(self):
        return '{}({})'.format(self.name, ', '.join(map(repr, self.args)))

class NamedPred(ASTNode):
    def __init__(self, name, args, body, restriction_env=None):
        super().__init__()
        self.name = name

        self.args = []
        self.arg_restrictions = []
        for arg in args:
            if type(arg) is VarRef:
                self.args.append(arg)
            elif type(arg) is Call:
                self.args.append(arg.args[0])
                self.arg_restrictions.append(Restriction([arg.args[0]], arg))
            else:
                raise Exception("Argument '{}' is not: VarRef, or Call!".format(arg))

        self.restriction_env = restriction_env or {}

        self.body = body

    def transform(self, transformer):
        return transformer.transform_NamedPred(self)

    def __repr__(self):
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

    def transform(self, transformer):
        return transformer.transform_Program(self)

    def __repr__(self):
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

    def __repr__(self):
        return '{} are {}'.format(', '.join(map(repr, self.restrict_vars)), self.pred)

