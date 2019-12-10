#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer

from pecan.lang.pecan_ir import *

class BooleanOptimizer(IRTransformer):
    def transform_Complement(self, node):
        if type(node.a) is Complement:
            # !(!P) is equivalent to P
            return self.transform(node.a.a)
        else:
            return Complement(self.transform(node.a))

