#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.optimizer.basic_optimizer import BasicOptimizer
from pecan.lang.optimizer.tools import VariableUsage

from pecan.lang.ir import *

class UnusedVariableOptimizer(BasicOptimizer):
    def transform_Exists(self, node: Exists):
        used_vars = VariableUsage().analyze(node.pred)

        new_var_refs = []
        new_conds = []

        for v, cond in zip(node.var_refs, node.conds):
            if v.var_name in used_vars:
                new_var_refs.append(v)
                new_conds.append(cond)
            else:
                self.changed = True

        if len(new_var_refs) == 0:
            return self.transform(node.pred)
        else:
            return Exists(new_var_refs, new_conds, self.transform(node.pred))

