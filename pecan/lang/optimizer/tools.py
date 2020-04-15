#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer

from pecan.lang.ir import *

class FreeVars(IRTransformer):
    def __init__(self):
        super().__init__()
        self.free_vars = set()

    def transform_VarRef(self, node: VarRef):
        self.free_vars.add(node.var_name)
        return super().transform_VarRef(node)

    def transform_Exists(self, node: Exists):
        res = super().transform_Exists(node)
        self.free_vars -= set(v.var_name for v in node.var_refs)
        return res

    def transform_FunctionExpression(self, node: FunctionExpression):
        new_name = self.transform(node.pred_name)
        new_args = []
        for i, arg in enumerate(node.args):
            # Don't look at the output result, it'll get quantified away
            if i == node.val_idx:
                new_args.append(arg)
            else:
                new_args.append(self.transform(arg))

        return FunctionExpression(new_name, new_args, node.val_idx).with_type(node.get_type())

    def transform_Conjunction(self, node):
        newA = super().transform(node.a)
        save = set(self.free_vars)
        newB = super().transform(node.b)
        self.free_vars = self.free_vars.union(save)
        return node

    def transform_Disjunction(self, node):
        newA = super().transform(node.a)
        save = set(self.free_vars)
        newB = super().transform(node.b)
        self.free_vars = self.free_vars.union(save)
        return node

    def analyze(self, node):
        self.free_vars = set()
        self.transform(node)
        return self.free_vars

class ExpressionFrequency(IRTransformer):
    def __init__(self):
        super().__init__()
        self.expr_frequency = {}

    def transform(self, node):
        if isinstance(node, IRExpression):
            if not node in self.expr_frequency:
                self.expr_frequency[node] = 1
            else:
                self.expr_frequency[node] += 1

        return super().transform(node)

    def count(self, node):
        self.expr_frequency = {}
        self.transform(node)
        return self.expr_frequency

class NodeSubstitution(IRTransformer):
    def __init__(self, subs_dict):
        super().__init__()
        self.subs_dict = subs_dict
        self.changed = False

    def transform(self, node):
        if node in self.subs_dict:
            self.changed = True
            return self.subs_dict[node]
        else:
            return super().transform(node)

class DepthAnalyzer(IRTransformer):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.max_depth = 0

    def transform(self, node):
        self.depth += 1
        res = super().transform(node)
        self.depth -= 1
        return res

    def transform_VarRef(self, node):
        # -1 because the current level doesn't "count"
        self.max_depth = max(self.depth - 1, self.max_depth)
        return node

    def transform_FunctionExpression(self, node):
        self.max_depth = max(self.depth - 1, self.max_depth)
        return node

    def count(self, node):
        self.max_depth = 0
        self.transform(node)
        return self.max_depth

class VariableUsage(IRTransformer):
    def __init__(self):
        super().__init__()
        self.used_vars = set()

    def transform(self, node):
        if isinstance(node, IRNode) and node.get_type() is not None:
            if node.get_type().get_restriction() is not None:
                self.transform(node.get_type().get_restriction())

        return super().transform(node)

    def transform_VarRef(self, node):
        self.used_vars.add(node.var_name)
        return node

    def analyze(self, node):
        self.used_vars = set()
        self.transform(node)
        return self.used_vars

