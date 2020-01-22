#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.optimizer.basic_optimizer import BasicOptimizer
from pecan.lang.optimizer.tools import VariableUsage

from pecan.lang.ir import *

class UnusedVariableOptimizer(BasicOptimizer):
    def transform_Exists(self, node: Exists):
        used_vars = VariableUsage().analyze(node.pred)

        if node.var.var_name in used_vars:
            return super().transform_Exists(node)
        else:
            self.changed = True
            return self.transform(node.pred)

