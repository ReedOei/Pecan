#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast import *
import pecan.lang.ir as ir

from pecan.lang.ast_transformer import AstTransformer
from pecan.lang.type_inference import *

class ASTToIR(AstTransformer):
    def __init__(self):
        super().__init__()
        self.prog = None # This will be set when we are transforming programs

    def transform_decl_type(self, t):
        if type(t) is RestrictionType:
            return RestrictionType(self.transform(t.restriction))
        else:
            return t

    def transform_Conjunction(self, node):
        return ir.Conjunction(self.transform(node.a), self.transform(node.b))

    def transform_Disjunction(self, node):
        return ir.Disjunction(self.transform(node.a), self.transform(node.b))

    def transform_Complement(self, node):
        return ir.Complement(self.transform(node.a))

    def transform_Iff(self, node):
        new_a = self.transform(node.a)
        new_b = self.transform(node.b)
        return ir.Conjunction(ir.Disjunction(ir.Complement(new_a), new_b), ir.Disjunction(ir.Complement(new_b), new_a)).with_original_node(node)

    def transform_Implies(self, node):
        new_a = self.transform(node.a)
        new_b = self.transform(node.b)
        return ir.Disjunction(ir.Complement(new_a), new_b).with_original_node(node)

    def transform_FormulaTrue(self, node):
        return ir.FormulaTrue()

    def transform_FormulaFalse(self, node):
        return ir.FormulaFalse()

    def transform_DirectiveSaveAut(self, node):
        return ir.DirectiveSaveAut(node.filename, node.pred_name)

    def transform_DirectiveSaveAutImage(self, node):
        return ir.DirectiveSaveAutImage(node.filename, node.pred_name)

    def transform_DirectiveContext(self, node):
        return ir.DirectiveContext(node.context_key, node.context_val)

    def transform_DirectiveEndContext(self, node):
        return ir.DirectiveEndContext(node.context_key)

    def transform_DirectiveAssertProp(self, node):
        return ir.DirectiveAssertProp(node.truth_val, node.pred_name)

    def transform_DirectiveLoadAut(self, node):
        return ir.DirectiveLoadAut(node.filename, node.aut_format, self.transform(node.pred))

    def transform_DirectiveImport(self, node):
        return ir.DirectiveImport(node.filename)

    def transform_DirectiveForget(self, node):
        return ir.DirectiveForget(node.var_name)

    def transform_DirectiveType(self, node):
        return ir.DirectiveType(self.transform(node.pred_ref), {self.transform(k): self.transform(v) for k, v, in node.val_dict.items()})

    def transform_DirectiveShowWord(self, node):
        return ir.DirectiveShowWord(self.transform(node.word_name), self.transform_decl_type(node.index_type), node.start_index, node.end_index)

    def transform_Add(self, node):
        return ir.Add(self.transform(node.a), self.transform(node.b))

    def transform_Sub(self, node):
        return ir.Sub(self.transform(node.a), self.transform(node.b))

    def transform_Mul(self, node):
        return ir.Mul(self.transform(node.a), self.transform(node.b))

    def transform_Div(self, node):
        return ir.Div(self.transform(node.a), self.transform(node.b))

    def transform_IntConst(self, node):
        return ir.IntConst(node.val)

    def transform_Equals(self, node):
        return ir.Equals(self.transform(node.a), self.transform(node.b))

    def transform_NotEquals(self, node):
        return ir.Complement(ir.Equals(self.transform(node.a), self.transform(node.b))).with_original_node(node)

    def transform_Less(self, node):
        return ir.Less(self.transform(node.a), self.transform(node.b))

    def transform_Greater(self, node):
        return ir.Less(self.transform(node.b), self.transform(node.a))

    def transform_LessEquals(self, node):
        new_a = self.transform(node.a)
        new_b = self.transform(node.b)
        return ir.Disjunction(ir.Less(new_a, new_b), ir.Equals(new_a, new_b))

    def transform_GreaterEquals(self, node):
        new_a = self.transform(node.a)
        new_b = self.transform(node.b)
        return ir.Disjunction(ir.Less(new_b, new_a), ir.Equals(new_a, new_b))

    def transform_Neg(self, node):
        return ir.Sub(IntConst(0), self.transform(node.a))

    def transform_Index(self, node):
        return ir.Index(node.var_name, self.transform(node.index_expr))

    def transform_IndexRange(self, node):
        return ir.IndexRange(node.var_name, self.transform(node.start), self.transform(node.end))

    def transform_EqualsCompareIndex(self, node):
        return ir.EqualsCompareIndex(node.is_equals, self.transform(node.index_a), self.transform(node.index_b))

    def transform_EqualsCompareRange(self, node):
        return ir.EqualsCompareRange(node.is_equals, self.transform(node.index_a), self.transform(node.index_b))

    def transform_Forall(self, node: Forall):
        # TODO: Make a `get_cond` method for this
        if node.cond is not None:
            return ir.Complement(ir.Exists(self.transform(node.cond), ir.Complement(self.transform(node.pred)))).with_original_node(node)
        else:
            return ir.Complement(ir.Exists(self.transform(node.var), ir.Complement(self.transform(node.pred)))).with_original_node(node)

    def transform_Exists(self, node: Exists):
        if node.cond is not None:
            return ir.Exists(self.transform(node.cond), self.transform(node.pred)).with_original_node(node)
        else:
            return ir.Exists(self.transform(node.var), self.transform(node.pred)).with_original_node(node)

    def transform_VarRef(self, node: VarRef):
        return ir.VarRef(node.var_name)

    def transform_AutLiteral(self, node):
        return ir.AutLiteral(node.aut)

    def transform_SpotFormula(self, node):
        return ir.SpotFormula(node.formula_str)

    def transform_Call(self, node):
        return ir.Call(node.name, [self.transform(arg) for arg in node.args])

    def transform_NamedPred(self, node):
        return ir.NamedPred(node.name, [self.transform(arg) for arg in node.args], self.transform(node.body), restriction_env=node.restriction_env)

    def transform_Program(self, node):
        # TODO: While `copy_defaults` will work here because of duck typing (node is an ast.prog.Program, not an ir.prog.Program), we should make come up with a better solution maybe?
        self.prog = ir.Program([]).copy_defaults(node)
        self.prog.defs = [self.transform(d) for d in node.defs]
        self.prog.restrictions = [{self.transform(k): list(map(self.transform, v)) for k, v in restrictions.items()} for restrictions in node.restrictions]
        self.prog.types = dict([self.transform_type(k, v) for k, v in node.types.items()])
        new_prog = self.prog
        self.prog = None
        return new_prog

    def transform_type(self, pred_ref, val_dict):
        return (self.transform(pred_ref), {self.transform(k): self.transform(v) for k, v in val_dict.items()})

    def transform_Restriction(self, node):
        return ir.Restriction(node.var_names, self.transform(node.pred))

