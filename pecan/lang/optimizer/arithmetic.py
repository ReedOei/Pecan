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

    def transform_Equals(self, node):
        # we can only do the following transformation once we know types, otherwise we will be unable to resolve the dynamic call to 'adder'
        if node.a.get_type() is not None and node.b.get_type() is not None:
            if type(node.a) is VarRef and type(node.b) is Add:
                self.changed = True
                return self.transform(Call('adder', [node.b.a, node.b.b, node.a]))
            elif type(node.b) is VarRef and type(node.a) is Add:
                self.changed = True
                return self.transform(Call('adder', [node.a.a, node.a.b, node.b]))
            # elif type(node.a) is VarRef and type(node.b) is Sub:
            #     self.changed = True
            #     return self.transform(Call('adder', [node.a, node.b.b, node.b.a]))
            # elif type(node.b) is VarRef and type(node.a) is Sub:
            #     self.changed = True
            #     return self.transform(Call('adder', [node.b, node.a.b, node.a.a]))

        return super().transform_Equals(node)

