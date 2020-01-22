#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.optimizer.basic_optimizer import BasicOptimizer
from pecan.lang.optimizer.tools import ExpressionFrequency, NodeSubstitution

from pecan.lang.ir import *

class CustomNodeSubstitution(NodeSubstitution):
    def transform_Exists(self, node: Exists):
        # Don't change the variable, or it could go out of scope too soon
        return Exists(node.var, self.transform(node.cond), self.transform(node.pred))

class RedundantVariableOptimizer(BasicOptimizer):
    def __init__(self, master_optimizer):
        super().__init__(master_optimizer)

        # At what level each variable becomes in scope.
        # This is useful so we can decide which of two variables to keep (the one which was declared higher up)
        self.decl_level = {}
        self.cur_level = 0

        self.subs = {}

        self.count = None

    def pre_optimize(self, node):
        self.decl_level = {}
        self.subs = {}
        self.cur_level = 0
        self.count = ExpressionFrequency().count(node)

    def post_optimize(self, node):
        return CustomNodeSubstitution(self.subs).transform(node)

    def transform_Equals(self, node):
        if node.a == node.b:
            return FormulaTrue()

        if type(node.a) is VarRef and type(node.b) is VarRef:
            if self.decl_level.get(node.a.var_name, -1) < self.decl_level.get(node.b.var_name, -1):
                self.changed = True
                self.subs[node.b] = self.subs.get(node.a, node.a)
            else:
                self.changed = True
                self.subs[node.a] = self.subs.get(node.b, node.b)

            return FormulaTrue()

        return super().transform_Equals(node)

    def transform_Exists(self, node: Exists):
        self.cur_level += 1

        self.decl_level[node.var.var_name] = self.cur_level
        result = super().transform_Exists(node)

        self.cur_level -= 1

        return result

