#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.pecan_ast.bool import *
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

    def evaluate_node(self, prog):
        if len(prog.get_restrictions(self.var.var_name)) > 0:
            constraints = reduce(Conjunction, prog.get_restrictions(self.var.var_name))
            new_pred = Implies(constraints, self.pred)
        else:
            new_pred = self.pred
        return Complement(Exists(self.var, Complement(self.with_cond(new_pred)))).evaluate(prog)

    def with_cond(self, pred):
        if self.cond is not None:
            return Implies(self.cond, pred)
        else:
            return pred

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

    def evaluate_node(self, prog):
        if len(prog.get_restrictions(self.var.var_name)) > 0:
            constraints = reduce(Conjunction, prog.get_restrictions(self.var.var_name))
            new_pred = Conjunction(constraints, self.pred)
        else:
            new_pred = self.pred

        return Projection(self.with_cond(new_pred).evaluate(prog), [self.var.var_name]).project()

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
