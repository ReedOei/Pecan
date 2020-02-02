#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

from pecan.lang.ir.bool import *

class Exists(IRPredicate):
    def __init__(self, var: VarRef, cond, pred):
        super().__init__()
        self.var = var
        self.cond = cond
        self.pred = pred

    def evaluate_node(self, prog):
        # TODO: Move to this to TypedIRLowering or something
        if len(prog.get_restrictions(self.var.var_name)) > 0:
            constraints = reduce(Conjunction, prog.get_restrictions(self.var.var_name))
            new_pred = Conjunction(constraints, self.pred)
        else:
            new_pred = self.pred

        if self.cond is not None:
            prog.restrict(self.var.var_name, self.cond)

        aut = self.with_cond(new_pred).evaluate(prog)
        res = aut.project([self.var])

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
            return '(∃{}. {})'.format(self.var, Conjunction(self.cond, self.pred))
        else:
            return '(∃{}. {})'.format(self.var, self.pred)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var == other.var and self.cond == other.cond and self.pred == other.pred

    def __hash__(self):
        return hash((self.var, self.cond, self.pred))

