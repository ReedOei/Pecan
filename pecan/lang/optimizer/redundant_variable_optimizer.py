#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.optimizer.basic_optimizer import BasicOptimizer
from pecan.lang.optimizer.tools import ExpressionFrequency, NodeSubstitution

from pecan.lang.ir import *

from functools import reduce

class CustomNodeSubstitution(NodeSubstitution):
    def transform_Exists(self, node: Exists):
        # Don't change the variable, or it could go out of scope too soon
        return Exists(node.var_refs, [self.transform(cond) for cond in node.conds], self.transform(node.pred))

class RedundantVariableOptimizer(BasicOptimizer):
    def __init__(self, master_optimizer):
        super().__init__(master_optimizer)

        # At what level each variable becomes in scope.
        # This is useful so we can decide which of two variables to keep (the one which was declared higher up)
        self.decl_level = {}
        self.cur_level = 0

        self.enabled = True

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

    def transform(self, node):
        if not isinstance(node, Conjunction):
            self.enabled = True
        return super().transform(node)

    def gather_conjuncts(self, node):
        res = []
        if isinstance(node.a, Conjunction):
            res += self.gather_conjuncts(node.a)
        else:
            res += [node.a]

        if isinstance(node.b, Conjunction):
            res += self.gather_conjuncts(node.b)
        else:
            res += [node.b]

        return res

    def transform_Conjunction(self, node):
        if self.enabled:
            conjuncts = self.gather_conjuncts(node)

            info = {}
            for conjunct in conjuncts:
                info.update(self.gather_info(conjunct))

            substituter = CustomNodeSubstitution(info)
            new_conjuncts = [ substituter.transform(conjunct) for conjunct in conjuncts ]
            self.changed |= substituter.changed

            new_node = reduce(Conjunction, new_conjuncts)

            self.enabled = False
            return super().transform(new_node)
        else:
            return super().transform_Conjunction(node)

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

        for v in node.var_refs:
            self.decl_level[v.var_name] = self.cur_level

        result = super().transform_Exists(node)

        self.cur_level -= 1

        return result

