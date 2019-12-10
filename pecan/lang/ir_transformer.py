#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.pecan_ir import *

class IRTransformer:
    def __init__(self):
        pass

    def transform(self, node):
        if type(node) is str:
            return node
        else:
            return node.transform(self).with_original_node(node.get_original_node())

    def transform_Conjunction(self, node):
        return Conjunction(self.transform(node.a), self.transform(node.b))

    def transform_Disjunction(self, node):
        return Disjunction(self.transform(node.a), self.transform(node.b))

    def transform_Complement(self, node):
        return Complement(self.transform(node.a))

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

    def transform_Add(self, node):
        return Add(self.transform(node.a), self.transform(node.b)).with_type(node.get_type())

    def transform_Sub(self, node):
        return Sub(self.transform(node.a), self.transform(node.b)).with_type(node.get_type())

    def transform_Mul(self, node):
        return Mul(self.transform(node.a), self.transform(node.b)).with_type(node.get_type())

    def transform_Div(self, node):
        return Div(self.transform(node.a), self.transform(node.b)).with_type(node.get_type())

    def transform_IntConst(self, node):
        return node

    def transform_Equals(self, node):
        return Equals(self.transform(node.a), self.transform(node.b))

    def transform_Less(self, node):
        return Less(self.transform(node.a), self.transform(node.b))

    def transform_Neg(self, node):
        return Neg(self.transform(node.a)).with_type(node.get_type())

    def transform_Index(self, node):
        return Index(node.var_name, self.transform(node.index_expr))

    def transform_IndexRange(self, node):
        return IndexRange(node.var_name, self.transform(node.start), self.transform(node.end))

    def transform_EqualsCompareIndex(self, node):
        return EqualsCompareIndex(node.is_equals, self.transform(node.index_a), self.transform(node.index_b))

    def transform_EqualsCompareRange(self, node):
        return EqualsCompareRange(node.is_equals, self.transform(node.index_a), self.transform(node.index_b))

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
        return NamedPred(node.name, [self.transform(arg) for arg in node.args], self.transform(node.body), restriction_env=node.restriction_env)

    def transform_Program(self, node):
        new_defs = [self.transform(d) for d in node.defs]
        new_restrictions = [{k: list(map(self.transform, v)) for k, v in restrictions.items()} for restrictions in node.restrictions]
        new_types = dict([self.transform_type(k, v) for k, v in node.types.items()])

        return Program(new_defs, restrictions=new_restrictions, types=new_types).copy_defaults(node)

    def transform_type(self, pred_ref, val_dict):
        return (pred_ref, val_dict)

    def transform_Restriction(self, node):
        return Restriction(node.var_names, self.transform(node.pred))

