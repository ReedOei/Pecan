#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

from pecan.lang.pecan_ast import *
from pecan.tools.automaton_tools import Projection

def extract_var_cond(var_pred):
    if type(var_pred) is VarRef:
        return (var_pred.var_name, None)
    elif type(var_pred) is Call:
        return (var_pred.args[0], var_pred)
    else:
        return (var_pred, None)

class Forall(Predicate):
    def __init__(self, var_pred, pred):
        super().__init__()
        self.var, cond = extract_var_cond(var_pred)

        if cond is not None:
            self.pred = Implies(cond, pred)
        else:
            self.pred = pred

    def evaluate_node(self, prog):
        if len(prog.get_restrictions(self.var)) > 0:
            constraints = reduce(Conjunction, prog.get_restrictions(self.var))
            new_pred = Implies(constraints, self.pred)
        else:
            new_pred = self.pred
        return Complement(Exists(self.var, Complement(new_pred))).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_Forall(self)

    def __repr__(self):
        return '(∀{} ({}))'.format(self.var, self.pred)

class Exists(Predicate):
    def __init__(self, var_pred, pred):
        super().__init__()
        self.var, cond = extract_var_cond(var_pred)

        if cond is not None:
            self.pred = Conjunction(cond, pred)
        else:
            self.pred = pred

    def evaluate_node(self, prog):
        if len(prog.get_restrictions(self.var)) > 0:
            constraints = reduce(Conjunction, prog.get_restrictions(self.var))
            new_pred = Conjunction(constraints, self.pred)
        else:
            new_pred = self.pred

        return Projection(new_pred.evaluate(prog), [self.var]).project()

    def transform(self, transformer):
        return transformer.transform_Exists(self)

    def __repr__(self):
        return '(∃{} ({}))'.format(self.var, self.pred)

