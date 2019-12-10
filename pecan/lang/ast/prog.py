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

    def insert_first(self, arg_name):
        return Call(self.var_name, [arg_name])

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

class Match:
    def __init__(self, pred_name=None, pred_args=None, match_any=False):
        if pred_args is None:
            pred_args = []

        self.pred_name = pred_name
        self.pred_args = pred_args
        self.match_any = match_any

    def arity(self):
        return len(self.pred_args)

    def unify(self, other):
        if other.match_any:
            return self
        if self.match_any:
            return other

        new_args = []
        if self.pred_name != other.pred_name or self.arity() != other.arity():
            raise Exception(f'Could not unify {self} and {other}')

        for arg1, arg2 in zip(self.pred_args, other.pred_args):
            if arg1 == 'any' and arg2 == 'any':
                new_args.append('any')
            elif arg1 == 'any' and arg2 != 'any':
                new_args.append(arg2)
            elif arg1 != 'any' and arg2 == 'any':
                new_args.append(arg1)
            else:
                if arg1 == arg2:
                    new_args.append(arg1)
                else:
                    raise Exception(f'Could not unify {self} and {other}: cannot unify {arg1} and {arg2}')

        return Match(self.pred_name, new_args)

    def actual_args(self):
        actual_args = []
        for arg in self.pred_args:
            if type(arg) is VarRef:
                actual_args.append(arg.var_name)
            elif type(arg) is str:
                actual_args.append(arg)
            else:
                raise Exception("Argument '{}' is not: string or VarRef!".format(arg))
        return actual_args

    def call_with(self, pred_name, unification, rest_args):
        if self.match_any:
            raise Exception(f'Predicate not found: {pred_name}')
        i = 0
        final_args = []
        for arg in self.actual_args():
            if arg == 'any':
                if i >= len(rest_args):
                    # TODO: We should check this in the linter probably
                    raise Exception(f'Not enough arguments to call {self}: {rest_args}')

                final_args.append(rest_args[i])
                i += 1
            else:
                final_args.append(unification.get(arg, arg))

        return Call(self.pred_name, final_args)

    def __repr__(self):
        return '{}({})'.format(self.pred_name, ', '.join(map(repr, self.pred_args)))

class Call(Predicate):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args if isinstance(args, list) else [args]

    def arity(self):
        return len(self.args)

    def match(self):
        return Match(self.name, self.args)

    def with_args(self, new_args):
        if len(new_args) == 0:
            return VarRef(self.name)
        else:
            return Call(self.name, new_args)

    def insert_first(self, new_arg):
        return Call(self.name, [new_arg] + self.actual_args())

    def actual_args(self):
        actual_args = []
        for arg in self.args:
            if type(arg) is VarRef:
                actual_args.append(arg.var_name)
            else:
                actual_args.append(arg)
        return actual_args

    def transform(self, transformer):
        return transformer.transform_Call(self)

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
                self.args.append(arg.var_name)
            elif type(arg) is str:
                self.args.append(arg)
            elif type(arg) is Call:
                self.args.append(arg.args[0])
                self.arg_restrictions.append(Restriction([arg.args[0]], arg.insert_first))
            else:
                raise Exception("Argument '{}' is not: string, VarRef, or a Call!".format(arg))

        self.restriction_env = restriction_env or {}

        self.body = body

    def transform(self, transformer):
        return transformer.transform_NamedPred(self)

    def __repr__(self):
        return '{}({}) := {}'.format(self.name, ', '.join(self.args), self.body)

class Program(ASTNode):
    def __init__(self, defs, *args, **kwargs):
        super().__init__()

        self.defs = defs
        self.preds = kwargs.get('preds', {})
        self.context = kwargs.get('context', {})
        self.restrictions = kwargs.get('restrictions', [{}])
        self.types = kwargs.get('types', {})
        self.parser = kwargs.get('parser', None) # This will be "filled in" in the main.py after we load a program
        self.debug = kwargs.get('debug', 0)
        self.quiet = kwargs.get('quiet', False)
        self.eval_level = kwargs.get('eval_level', 0)
        self.result = kwargs.get('result', None)
        self.search_paths = kwargs.get('search_paths', [])
        self.fresh_counter = kwargs.get('fresh_counter', 0)
        self.loader = kwargs.get('loader', None)

    def copy_defaults(self, other_prog):
        self.context = other_prog.context
        self.parser = other_prog.parser
        self.debug = other_prog.debug
        self.quiet = other_prog.quiet
        self.eval_level = other_prog.eval_level
        self.result = other_prog.result
        self.search_paths = other_prog.search_paths
        self.fresh_counter = other_prog.fresh_counter
        self.loader = other_prog.loader
        return self

    def transform(self, transformer):
        return transformer.transform_Program(self)

    def __repr__(self):
        return repr(self.defs)

class Restriction(ASTNode):
    def __init__(self, var_names, pred):
        super().__init__()
        self.var_names = []
        for var_name in var_names if isinstance(var_names, list) else [var_names]:
            if type(var_name) is str:
                self.var_names.append(var_name)
            elif type(var_name) is VarRef:
                self.var_names.append(var_name.var_name)
            else:
                raise Exception("Argument '{}' is not a valid var name (string or VarRef)".format(var_name))
        self.pred = pred

    def transform(self, transformer):
        return transformer.transform_Restriction(self)

    def __repr__(self):
        return '{} are {}'.format(', '.join(self.var_names), self.pred.insert_first('*')) # TODO: Improve this

