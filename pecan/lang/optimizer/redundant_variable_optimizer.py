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

    def pre_optimize(self, node):
        self.decl_level = {}
        self.cur_level = 0

    # TODO: Make this track information more completely. For the moment, it'll only handle truly obvious cases.
    def gather_info(self, node):
        subs = {}

        if type(node) is Equals:
            if type(node.a) is VarRef and type(node.b) is VarRef:
                if node.a.var_name in self.decl_level and node.b.var_name in self.decl_level:
                    if self.decl_level[node.a.var_name] < self.decl_level[node.b.var_name]:
                        subs[node.b] = node.a
                    else:
                        subs[node.a] = node.b

        return subs

    def transform_Conjunction(self, node):
        orig_a = self.transform(node.a)
        orig_b = self.transform(node.b)

        info = self.gather_info(orig_a)
        substituter = CustomNodeSubstitution(info)

        new_a = substituter.transform(orig_a)
        new_b = substituter.transform(orig_b)

        self.changed |= substituter.changed

        return Conjunction(new_a, new_b)

    def transform_Complement(self, node):
        # Clear out the level dictionary, because the complement means that variables outside should not interact with variables inside
        # TODO: I think...? at the very least, it's safe to do clear it out, because we'll just optimize a little less
        temp = self.decl_level
        self.decl_level = {}
        result = super().transform_Complement(node)
        self.decl_level = temp

        return result

    def transform_Exists(self, node: Exists):
        self.cur_level += 1

        self.decl_level[node.var.var_name] = self.cur_level
        result = super().transform_Exists(node)

        self.cur_level -= 1

        return result

