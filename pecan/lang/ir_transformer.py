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

    def transform_DirectiveAcceptingWord(self, node):
        return node

    def transform_DirectiveShuffle(self, node):
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
        self.current_program.praline_defs = {k: self.transform(d) for k, d in node.praline_defs.items()}
        self.current_program.praline_envs = [{k: self.transform(d) for k, d in env} for env in node.praline_envs]
        new_program = self.current_program
        self.current_program = None
        return new_program

    def transform_type(self, pred_ref, val_dict):
        return (pred_ref, val_dict)

    def transform_Restriction(self, node):
        return Restriction(list(map(self.transform, node.restrict_vars)), self.transform(node.pred))

    def transform_FunctionExpression(self, node):
        return FunctionExpression(node.pred_name, [self.transform(arg) for arg in node.args], node.val_idx).with_type(node.get_type())

    def transform_PralineDisplay(self, node):
        return PralineDisplay(self.transform(node.term))

    def transform_PralineExecute(self, node):
        return PralineExecute(self.transform(node.term))

    def transform_PralineDef(self, node):
        return PralineDef(self.transform(node.name), list(map(self.transform, node.args)), self.transform(node.body))

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
        return PralineList(self.transform(node.a), self.transform(node.b))

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

    def transform_PralineMatchTuple(self, node):
        return PralineMatchTuple([self.transform(v) for v in node.vals])

    def transform_PralineMatchVar(self, node):
        return PralineMatchVar(self.transform(node.var))

    def transform_PralineIf(self, node):
        return PralineIf(self.transform(node.cond), self.transform(node.e1), self.transform(node.e2))

    def transform_PralinePecanTerm(self, node):
        return PralinePecanTerm(self.transform(node.pecan_term))

    def transform_PralineLambda(self, node):
        return PralineLambda(list(map(self.transform, node.params)), self.transform(node.body))

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

    def transform_PralineEq(self, node):
        return PralineEq(self.transform(node.a), self.transform(node.b))

    def transform_PralineNe(self, node):
        return PralineNe(self.transform(node.a), self.transform(node.b))

    def transform_PralineGe(self, node):
        return PralineGe(self.transform(node.a), self.transform(node.b))

    def transform_PralineLe(self, node):
        return PralineLe(self.transform(node.a), self.transform(node.b))

    def transform_PralineGt(self, node):
        return PralineGt(self.transform(node.a), self.transform(node.b))

    def transform_PralineLt(self, node):
        return PralineLt(self.transform(node.a), self.transform(node.b))

    def transform_PralineAutomaton(self, node):
        return PralineAutomaton(node.aut)

    def transform_Closure(self, node):
        new_env = {k: self.transform(v) for k, v in node.env.items()}
        new_args = [self.transform(arg) for arg in node.args]
        new_body = self.transform(node.body)
        return Closure(new_env, new_args, new_body)

    def transform_Builtin(self, node):
        return node

    def transform_PralineDo(self, node):
        return PralineDo([self.transform(t) for t in node.terms])

