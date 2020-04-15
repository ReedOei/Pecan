#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.ast_to_ir import ASTToIR

from pecan.lang.ast import *

class PralineToPecan(IRTransformer):
    def __init__(self):
        super().__init__()
        self.ast_to_ir = ASTToIR()

    def to_ir(self, node):
        return self.ast_to_ir.transform(node)

    def transform_PralineDisplay(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineExecute(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineDef(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineApp(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineAdd(self, node):
        return self.to_ir(Add(self.transform(node.a), self.transform(node.b)))

    def transform_PralineSub(self, node):
        return self.to_ir(Sub(self.transform(node.a), self.transform(node.b)))

    def transform_PralineMul(self, node):
        return self.to_ir(Mul(self.transform(node.a), self.transform(node.b)))

    def transform_PralineDiv(self, node):
        return self.to_ir(Div(self.transform(node.a), self.transform(node.b)))

    def transform_PralineExponent(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineNeg(self, node):
        return self.to_ir(Neg(self.transform(node.a), self.transform(node.b)))

    def transform_PralineList(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineMatch(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineMatchArm(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineMatchInt(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineMatchString(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineMatchList(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineMatchVar(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineIf(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralinePecanTerm(self, node):
        # Note: We can't do this because we need to know the environment to evaluate in.
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralinePecanLiteral(self, node):
        return node.get_term()

    def transform_PralineLambda(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineLetPecan(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineLet(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineTuple(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineVar(self, node):
        return self.to_ir(VarRef(node.var_name))

    def transform_PralineInt(self, node):
        return self.to_ir(IntConst(node.val))

    def transform_PralineString(self, node):
        return self.to_ir(VarRef(node.val))

    def transform_PralineBool(self, node):
        return self.to_ir(BoolConst(node.val))

    def transform_PralineDo(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

    def transform_PralineAutomaton(self, node):
        raise Exception('"{}" cannot be translated into to Pecan'.format(node))

