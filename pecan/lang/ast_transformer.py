#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast import *

class AstTransformer:
    def __init__(self):
        pass

    def transform(self, node):
        if type(node) is str:
            return node
        else:
            return node.transform(self)

    def transform_Conjunction(self, node):
        return Conjunction(self.transform(node.a), self.transform(node.b))

    def transform_Disjunction(self, node):
        return Disjunction(self.transform(node.a), self.transform(node.b))

    def transform_Complement(self, node):
        return Complement(self.transform(node.a))

    def transform_Iff(self, node):
        return Iff(self.transform(node.a), self.transform(node.b))

    def transform_Implies(self, node):
        return Implies(self.transform(node.a), self.transform(node.b))

    def transform_FormulaTrue(self, node):
        return node

    def transform_FormulaFalse(self, node):
        return node

    def transform_DirectiveSaveAut(self, node):
        return node

    def transform_DirectiveSaveAutImage(self, node):
        return node

    def transform_DirectiveContext(self, node):
        return node

    def transform_DirectiveEndContext(self, node):
        return node

    def transform_DirectiveAssertProp(self, node):
        return node

    def transform_DirectiveLoadAut(self, node):
        return node

    def transform_DirectiveImport(self, node):
        return node

    def transform_DirectiveForget(self, node):
        return node

    def transform_DirectiveType(self, node):
        return node

    def transform_DirectiveShowWord(self, node):
        return node

    def transform_DirectiveAcceptingWord(self, node):
        return node

    def transform_DirectiveShuffle(self, node):
        return node

    def transform_Add(self, node):
        return Add(self.transform(node.a), self.transform(node.b))

    def transform_Sub(self, node):
        return Sub(self.transform(node.a), self.transform(node.b))

    def transform_Mul(self, node):
        return Mul(self.transform(node.a), self.transform(node.b))

    def transform_Div(self, node):
        return Div(self.transform(node.a), self.transform(node.b))

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

    def transform_Index(self, node):
        return Index(node.var_name, self.transform(node.index_expr))

    def transform_IndexRange(self, node):
        return IndexRange(node.var_name, self.transform(node.start), self.transform(node.end))

    def transform_EqualsCompareIndex(self, node):
        return EqualsCompareIndex(node.is_equals, self.transform(node.index_a), self.transform(node.index_b))

    def transform_EqualsCompareRange(self, node):
        return EqualsCompareRange(node.is_equals, self.transform(node.index_a), self.transform(node.index_b))

    def transform_Forall(self, node: Forall):
        if node.cond is not None:
            return Forall(node.cond, self.transform(node.pred))
        else:
            return Forall(node.var, self.transform(node.pred))

    def transform_Exists(self, node: Exists):
        if node.cond is not None:
            return Exists(node.cond, self.transform(node.pred))
        else:
            return Exists(node.var, self.transform(node.pred))

    def transform_VarRef(self, node: VarRef):
        return node

    def transform_AutLiteral(self, node):
        return node

    def transform_SpotFormula(self, node):
        return node

    def transform_Call(self, node):
        return Call(node.name, [self.transform(arg) for arg in node.args])

    def transform_NamedPred(self, node):
        new_args = [self.transform(arg) for arg in node.args]
        new_restrictions = {self.transform(var): self.transform(restriction) for var, restriction in node.arg_restrictions.items()}
        return NamedPred(node.name, new_args, new_restrictions, self.transform(node.body))

    def transform_Program(self, node):
        new_defs = [self.transform(d) for d in node.defs]
        new_restrictions = [{k: list(map(self.transform, v)) for k, v in restrictions.items()} for restrictions in node.restrictions]
        new_types = dict([self.transform_type(k, v) for k, v in node.types.items()])

        return Program(new_defs, restrictions=new_restrictions, types=new_types).copy_defaults(node)

    def transform_type(self, pred_ref, val_dict):
        return (pred_ref, val_dict)

    def transform_Restriction(self, node):
        return Restriction(list(map(self.transform, node.var_names)), self.transform(node.pred))

    def transform_FunctionExpression(self, node):
        return FunctionExpression(node.pred_name, list(map(self.transform, node.args)), node.val_idx)

    def transform_PralineDisplay(self, node):
        return PralineDisplay(self.transform(node.term))

    def transform_PralineExecute(self, node):
        return PralineExecute(self.transform(node.term))

    def transform_PralineDef(self, node):
        return PralineDef(reduce(PralineApp, [self.transform(node.name)] + list(map(self.transform, node.args))), self.transform(node.body))

    def transform_PralineCompose(self, node):
        return PralineCompose(self.transform(node.f), self.transform(node.g))

    def transform_PralineApp(self, node):
        return PralineApp(self.transform(node.receiver), self.transform(node.arg))

    def transform_PralineAdd(self, node):
        return PralineAdd(self.transform(node.a), self.transform(node.b))

    def transform_PralineDiv(self, node):
        return PralineDiv(self.transform(node.a), self.transform(node.b))

    def transform_PralineSub(self, node):
        return PralineSub(self.transform(node.a), self.transform(node.b))

    def transform_PralineMul(self, node):
        return PralineMul(self.transform(node.a), self.transform(node.b))

    def transform_PralineExponent(self, node):
        return PralineExponent(self.transform(node.a), self.transform(node.b))

    def transform_PralineNeg(self, node):
        return PralineNeg(self.transform(node.a))

    def transform_PralineList(self, node):
        return PralineList(self.transform(node.head), self.transform(node.tail))

    def transform_PralineMatch(self, node):
        return PralineMatch(self.transform(node.t), list(map(self.transform, node.arms)))

    def transform_PralineMatchArm(self, node):
        return PralineMatchArm(self.transform(node.pat), self.transform(node.expr))

    def transform_PralineMatchInt(self, node):
        return PralineMatchInt(self.transform(node.val))

    def transform_PralineMatchString(self, node):
        return PralineMatchString(self.transform(node.val))

    def transform_PralineMatchList(self, node):
        return PralineMatchList(self.transform(node.head), self.transform(node.tail))

    def transform_PralineMatchVar(self, node):
        return PralineMatchVar(self.transform(node.var))

    def transform_PralineIf(self, node):
        return PralineIf(self.transform(node.cond), self.transform(node.e1), self.transform(node.e2))

    def transform_PralinePecanTerm(self, node):
        return PralinePecanTerm(self.transform(node.pecan_term))

    def transform_PralineLambda(self, node):
        return PralineLambda(reduce(PralineApp, list(map(self.transform, node.params))), self.transform(node.body))

    def transform_PralineLetPecan(self, node):
        return PralineLetPecan(self.transform(node.var), self.transform(node.pecan_term), self.transform(node.body))

    def transform_PralineLet(self, node):
        return PralineLetPecan(self.transform(node.var), self.transform(node.expr), self.transform(node.body))

    def transform_PralineTuple(self, node):
        return PralineTuple(list(map(self.transform, node.vals)))

    def transform_PralineVar(self, node):
        return PralineVar(node.var_name)

    def transform_PralineInt(self, node):
        return PralineInt(node.val)

    def transform_PralineString(self, node):
        return PralineString(node.val)

    def transform_PralineBool(self, node):
        return PralineBool(node.val)

