#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast_transformer import AstTransformer
from pecan.lang.pecan_ast import *

class TypeInferer(AstTransformer):
    def __init__(self, prog):
        super().__init__()
        self.prog = prog

    def transform_Add(self, node):
        return Add(self.transform(node.a), self.transform(node.b), param=node.param)

    def transform_Sub(self, node):
        return Sub(self.transform(node.a), self.transform(node.b), param=node.param)

    def transform_Mul(self, node):
        return Mul(self.transform(node.a), self.transform(node.b), param=node.param)

    def transform_Div(self, node):
        return Div(self.transform(node.a), self.transform(node.b), param=node.param)

    def transform_IntConst(self, node):
        return node

    def transform_Equals(self, node):
        return Equals(self.transform(node.a), self.transform(node.b))

    def transform_NotEquals(self, node):
        return NotEquals(self.transform(node.a), self.transform(node.b))

    def transform_Less(self, node):
        return Less(self.transform(node.a), self.transform(node.b))

    def transform_Greater(self, node):
        return Greater(self.transform(node.a), self.transform(node.b))

    def transform_LessEquals(self, node):
        return LessEquals(self.transform(node.a), self.transform(node.b))

    def transform_GreaterEquals(self, node):
        return GreaterEquals(self.transform(node.a), self.transform(node.b))

    def transform_Neg(self, node):
        return Neg(self.transform(node.a))

    def transform_Call(self, node):
        return prog.Call(node.name, [self.transform(arg) for arg in node.args])
