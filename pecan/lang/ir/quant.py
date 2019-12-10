#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir.bool import *
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

class Exists(IRPredicate):
    def __init__(self, var_pred, pred):
        super().__init__()
        self.var, self.cond = extract_var_cond(var_pred)
        self.pred = pred

    def evaluate_node(self, prog):
        if len(prog.get_restrictions(self.var.var_name)) > 0:
            constraints = reduce(Conjunction, prog.get_restrictions(self.var.var_name))
            new_pred = Conjunction(constraints, self.pred)
        else:
            new_pred = self.pred

        if self.cond is not None:
            prog.restrict(self.var.var_name, self.cond)

        res = Projection(self.with_cond(new_pred).evaluate(prog), [self.var.var_name]).project()

        if self.cond is not None:
            prog.forget(self.var.var_name)

        return res

    def with_cond(self, pred):
        if self.cond is not None:
            return Conjunction(self.cond, pred)
        else:
            return pred

    def transform(self, transformer):
        return transformer.transform_Exists(self)

    def __repr__(self):
        if self.cond is None:
            return '(∃{} ({}))'.format(self.var, self.pred)
        else:
            return '(∃{} {})'.format(self.var, Conjunction(self.cond, self.pred))

