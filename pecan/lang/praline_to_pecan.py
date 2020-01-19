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

    def transform_PralineCompose(self, node):
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
        return node.pecan_term

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
        if node.val:
            return self.to_ir(FormulaTrue())
        else:
            return self.to_ir(FormulaFalse())

    def transform_PralineEq(self, node):
        return self.to_ir(Equals(self.transform(node.a), self.transform(node.b)))

    def transform_PralineNe(self, node):
        return self.to_ir(NotEquals(self.transform(node.a), self.transform(node.b)))

    def transform_PralineGe(self, node):
        return self.to_ir(GreaterEquals(self.transform(node.a), self.transform(node.b)))

    def transform_PralineLe(self, node):
        return self.to_ir(LessEquals(self.transform(node.a), self.transform(node.b)))

    def transform_PralineGt(self, node):
        return self.to_ir(Greater(self.transform(node.a), self.transform(node.b)))

    def transform_PralineLt(self, node):
        return self.to_ir(Less(self.transform(node.a), self.transform(node.b)))

    def transform_PralineAutomaton(self, node):
        return self.to_ir(AutLiteral(node.aut))

