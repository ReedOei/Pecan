#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer

from pecan.lang.ir import *

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

