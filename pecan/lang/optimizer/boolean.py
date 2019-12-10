#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer

from pecan.lang.pecan_ir import *

class BooleanOptimizer(IRTransformer):
    def transform_Complement(self, node):
        if type(node.a) is Complement:
            # !(!P) is equivalent to P
            return self.transform(node.a.a)

        # DeMorgan's Laws: Pushing complements down seems to help
        elif type(node.a) is Conjunction:
            return self.transform(Disjunction(Complement(node.a.a), Complement(node.a.b)))
        elif type(node.a) is Disjunction:
            return self.transform(Conjunction(Complement(node.a.a), Complement(node.a.b)))

        else:
            return Complement(self.transform(node.a))

