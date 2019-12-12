#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

from pecan.lang.ir.bool import *
from pecan.tools.automaton_tools import Projection

class Exists(IRPredicate):
    def __init__(self, var: VarRef, cond, pred):
        super().__init__()
        self.var = var
        self.cond = cond.with_parent(self) if cond is not None else None
        self.pred = pred.with_parent(self)

    def evaluate_node(self, prog):
        # TODO: Move to this to TypedIRLowering or something
        if len(prog.get_restrictions(self.var.var_name)) > 0:
            constraints = reduce(Conjunction, prog.get_restrictions(self.var.var_name))
            new_pred = Conjunction(constraints, self.pred).with_parent(self)
        else:
            new_pred = self.pred

        if self.cond is not None:
            prog.restrict(self.var.var_name, self.cond)

        aut = self.with_cond(new_pred).evaluate(prog)
        res = Projection(aut, [self.var.var_name]).project()

        if self.cond is not None:
            prog.forget(self.var.var_name)

        return res

    def with_cond(self, pred):
        if self.cond is None:
            return pred
        else:
            return Conjunction(self.cond, pred)

    def transform(self, transformer):
        return transformer.transform_Exists(self)

    def __repr__(self):
        if self.cond is not None:
            return '(∃{} {})'.format(self.var, Conjunction(self.cond, self.pred))
        else:
            return '(∃{} {})'.format(self.var, self.pred)

