#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir import *

class IRTransformer:
    def __init__(self):
        self.current_program = None

    def transform(self, node):
        if node is None:
            return None
        elif type(node) is str:
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

    def transform_DirectiveAcceptingWord(self, node):
        return node

    def transform_Add(self, node):
        return Add(self.transform(node.a), self.transform(node.b)).with_type(node.get_type())

    def transform_Sub(self, node):
        return Sub(self.transform(node.a), self.transform(node.b)).with_type(node.get_type())

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
        return Exists(self.transform(node.var), self.transform(node.cond), self.transform(node.pred))

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
        return NamedPred(node.name, new_args, new_restrictions, self.transform(node.body), restriction_env=node.restriction_env, body_evaluated=node.body_evaluated)

    def transform_Program(self, node):
        self.current_program = Program([]).copy_defaults(node)
        self.current_program.defs = [self.transform(d) for d in node.defs]
        self.current_program.restrictions = [{k: list(map(self.transform, v)) for k, v in restrictions.items()} for restrictions in node.restrictions]
        self.current_program.types = dict([self.transform_type(k, v) for k, v in node.types.items()])
        self.current_program.preds = {k: self.transform(d) for k, d in node.preds.items()}
        new_program = self.current_program
        self.current_program = None
        return new_program

    def transform_type(self, pred_ref, val_dict):
        return (pred_ref, val_dict)

    def transform_Restriction(self, node):
        return Restriction(list(map(self.transform, node.restrict_vars)), self.transform(node.pred))

    def transform_FunctionExpression(self, node):
        return FunctionExpression(node.pred_name, [self.transform(arg) for arg in node.args], node.val_idx)

