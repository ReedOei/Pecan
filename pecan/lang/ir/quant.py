#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from functools import reduce

from pecan.lang.ir.bool import *

class Exists(IRPredicate):
    def __init__(self, var_refs, conds, pred):
        super().__init__()
        self.var_refs = var_refs
        self.conds = conds
        self.pred = pred

    def evaluate_node(self, prog):
        for v, cond in zip(self.var_refs, self.conds):
            if cond is not None:
                prog.restrict(v.var_name, cond)

        all_constraints = self.get_prog_constraints(prog)
        aut = self.with_cond(all_constraints + self.conds, self.pred).evaluate(prog)
        res = aut.project(self.var_refs, prog.get_var_map())

        for v, cond in zip(self.var_refs, self.conds):
            if cond is not None:
                prog.forget(v.var_name)

        return res

    def get_prog_constraints(self, prog):
        all_constraints = []

        for v in self.var_refs:
            all_constraints.extend(prog.get_restrictions(v.var_name))

        return all_constraints

    def with_cond(self, conds, pred):
        cond = self.build_cond(set(conds))
        if cond is None:
            return pred
        else:
            return Conjunction(cond, pred)

    def transform(self, transformer):
        return transformer.transform_Exists(self)

    def build_cond(self, conds):
        filtered_cs = [c for c in conds if c is not None]

        if len(filtered_cs) == 0:
            return None
        else:
            return reduce(Conjunction, [c for c in conds if c is not None])

    def __repr__(self):
        return '(∃{}. {})'.format(self.var_refs, self.with_cond(self.conds, self.pred))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.var_refs == other.var_refs and self.conds == other.conds and self.pred == other.pred

    def __hash__(self):
        return hash((tuple(self.var_refs), tuple(self.conds), self.pred))

