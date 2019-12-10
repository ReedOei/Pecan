#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.optimizer.basic_optimizer import BasicOptimizer

from pecan.lang.ir import *

class ArithmeticOptimizer(BasicOptimizer):
    def constant_eq(self, node, val):
        return type(node) is IntConst and node.val == val

    def transform_Add(self, node):
        if self.constant_eq(node.a, 0):
            self.changed = True
            return self.transform(node.b)
        elif self.constant_eq(node.b, 0):
            self.changed = True
            return self.transform(node.a)
        else:
            return Add(self.transform(node.a), self.transform(node.b)).with_type(node.get_type())

    def transform_Sub(self, node):
        if self.constant_eq(node.b, 0):
            self.changed = True
            return self.transform(node.a)
        else:
            return Sub(self.transform(node.a), self.transform(node.b)).with_type(node.get_type())

