#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast.bool import *
from pecan.tools.automaton_tools import Projection

def to_ref(var_ref):
    if type(var_ref) is VarRef:
        return var_ref
    else:
        return VarRef(var_ref)

def extract_var_cond(var_pred):
    if type(var_pred) is Call:
        return to_ref(var_pred.args[0]), var_pred
    else:
        return to_ref(var_pred), None

class Forall(Predicate):
    def __init__(self, var_pred, pred):
        super().__init__()
        self.var, self.cond = extract_var_cond(var_pred)
        self.pred = pred

    def transform(self, transformer):
        return transformer.transform_Forall(self)

    def __repr__(self):
        if self.cond is None:
            return '(∀{} ({}))'.format(self.var, self.pred)
        else:
            return '(∀{} {})'.format(self.var, Implies(self.cond, self.pred))

class Exists(Predicate):
    def __init__(self, var_pred, pred):
        super().__init__()
        self.var, self.cond = extract_var_cond(var_pred)
        self.pred = pred

    def transform(self, transformer):
        return transformer.transform_Exists(self)

    def __repr__(self):
        if self.cond is None:
            return '(∃{} ({}))'.format(self.var, self.pred)
        else:
            return '(∃{} {})'.format(self.var, Conjunction(self.cond, self.pred))

