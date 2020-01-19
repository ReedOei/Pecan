#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir import *

from pecan.lang.ir_transformer import IRTransformer

class IRSubstitution(IRTransformer):
    def __init__(self, subs):
        super().__init__()
        self.subs = subs

    def transform_VarRef(self, node):
        if node.var_name in self.subs:
            return self.subs[node.var_name]
        else:
            return node

    def transform_Call(self, node):
        if node.name in self.subs:
            if type(self.subs[node.name]) is PralineString:
                return Call(self.subs[node.name].get_value(), [self.transform(arg) for arg in node.args]).with_type(node.get_type())
            else:
                raise Exception('Cannot substitute a non-string for a function name in "{}"; subs: {}'.format(node, self.subs))
        else:
            return super().transform_Call(node)

