#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast import *
import pecan.lang.ir as ir

from pecan.lang.ast_transformer import AstTransformer
from pecan.lang.type_inference import RestrictionType

def to_ref(var_ref):
    if type(var_ref) is ir.VarRef:
        return ir.VarRef(var_ref.var_name)
    else:
        return var_ref

def extract_var_cond(var_pred):
    if type(var_pred) is ir.Call:
        return to_ref(var_pred.args[0]), var_pred
    else:
        return to_ref(var_pred), None

class ASTToIR(AstTransformer):
    def __init__(self):
        super().__init__()
        self.prog = None # This will be set when we are transforming programs
        self.expr_depth = 0

    def transform_decl_type(self, t):
        if type(t) is Call:
            return RestrictionType(self.transform(t))
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
        return ir.DirectiveType(self.transform_decl_type(node.pred_ref), {self.transform(k): self.transform(v) for k, v, in node.val_dict.items()})

    def transform_DirectiveAcceptingWord(self, node):
        return ir.DirectiveAcceptingWord(node.pred_name)

    def transform_DirectiveShuffle(self, node):
        return ir.DirectiveShuffle(node.disjunction, self.transform(node.pred_a), self.transform(node.pred_b), self.transform(node.output_pred))

    def transform_Add(self, node):
        self.expr_depth += 1
        res = ir.Add(self.transform(node.a), self.transform(node.b))
        self.expr_depth -= 1
        return res

    def transform_Sub(self, node):
        self.expr_depth += 1
        res = ir.Sub(self.transform(node.a), self.transform(node.b))
        self.expr_depth -= 1
        return res

    def transform_Mul(self, node):
        if node.is_int:
            return ir.IntConst(node.evaluate_int(self.prog))

        # We are guaranteed that node.a will be an integer, so we don't need to worry about transforming it
        c = node.a.evaluate_int(prog)  # copy of a

        negative = False

        if c == 0:
            return ir.IntConst(0)

        if c < 0:
            negative = True
            c = -c

        self.expr_depth += 1
        power = self.transform(node.b)
        self.expr_depth -= 1

        s = ir.IntConst(0)
        while True:
            if c & 1 == 1:
                s = ir.Add(power, s)
            c = c // 2
            if c <= 0:
                break
            power = ir.Add(power, power)

        if negative:
            return ir.Sub(ir.IntConst(0), s).with_original_node(node)
        else:
            return s.with_original_node(node)

    def transform_Div(self, node):
        self.expr_depth += 1
        res = ir.Div(self.transform(node.a), self.transform(node.b))
        self.expr_depth -= 1
        return res

    def transform_IntConst(self, node):
        return ir.IntConst(node.val)

    def transform_Equals(self, node):
        self.expr_depth += 1
        res = ir.Equals(self.transform(node.a), self.transform(node.b))
        self.expr_depth -= 1
        return res

    def transform_NotEquals(self, node):
        return ir.Complement(self.transform(Equals(node.a, node.b))).with_original_node(node)

    def transform_Less(self, node):
        self.expr_depth += 1
        res = ir.Less(self.transform(node.a), self.transform(node.b))
        self.expr_depth -= 1
        return res

    def transform_Greater(self, node):
        return self.transform(Less(node.b, node.a)).with_original_node(node)

    def transform_LessEquals(self, node):
        return self.transform(Disjunction(Less(node.a, node.b), Equals(node.a, node.b))).with_original_node(node)

    def transform_GreaterEquals(self, node):
        return self.transform(Disjunction(Less(node.b, node.a), Equals(node.a, node.b))).with_original_node(node)

    def transform_Neg(self, node):
        return self.transform(Sub(IntConst(0), node.a)).with_original_node(node)

    def transform_Index(self, node):
        self.expr_depth += 1
        res = ir.Index(node.var_name, self.transform(node.index_expr))
        self.expr_depth -= 1
        return res

    def transform_IndexRange(self, node):
        self.expr_depth += 1
        res = ir.IndexRange(node.var_name, self.transform(node.start), self.transform(node.end))
        self.expr_depth -= 1
        return res

    def transform_EqualsCompareIndex(self, node):
        self.expr_depth += 1
        res = ir.EqualsCompareIndex(node.is_equals, self.transform(node.index_a), self.transform(node.index_b))
        self.expr_depth -= 1
        return res

    def transform_EqualsCompareRange(self, node):
        res = ir.EqualsCompareRange(node.is_equals, self.transform(node.index_a), self.transform(node.index_b))
        self.expr_depth -= 1
        return res

    def transform_Forall(self, node: Forall):
        if node.cond is not None:
            var, cond = extract_var_cond(self.transform(node.cond))
        else:
            var, cond = extract_var_cond(self.transform(node.var))

        if cond is not None:
            return ir.Complement(ir.Exists(var, cond, ir.Complement(self.transform(node.pred)))).with_original_node(node)
        else:
            return ir.Complement(ir.Exists(var, None, ir.Complement(self.transform(node.pred)))).with_original_node(node)

    def transform_Exists(self, node: Exists):
        if node.cond is not None:
            var, cond = extract_var_cond(self.transform(node.cond))
        else:
            var, cond = extract_var_cond(self.transform(node.var))

        if cond is not None:
            return ir.Exists(var, cond, self.transform(node.pred)).with_original_node(node)
        else:
            return ir.Exists(var, None, self.transform(node.pred)).with_original_node(node)

    def transform_VarRef(self, node: VarRef):
        return ir.VarRef(node.var_name)

    def transform_AutLiteral(self, node):
        return ir.AutLiteral(node.aut)

    def transform_SpotFormula(self, node):
        return ir.SpotFormula(node.formula_str)

    def transform_Call(self, node):
        self.expr_depth += 1
        new_args = [self.transform(arg) for arg in node.args]
        self.expr_depth -= 1
        # This means we are inside an expression, and are to be treated as though we are an expression, not a predicate
        if self.expr_depth > 0:
            idx = -1
            for i, arg in enumerate(new_args):
                if type(arg) is ir.VarRef and arg.var_name == '_':
                    if idx != -1:
                        raise Exception('Multiple outputs specified for function expression: {}({})'.format(node.name, node.args))
                    idx = i

            # If no '_' is passed, then assume the output is the last arguments. This lets us write things like "add(a, b)" and get "add(a, b, _)"
            if idx == -1:
                idx = len(new_args)
                new_args.append(ir.VarRef('_'))

            return ir.FunctionExpression(node.name, new_args, idx)
        else:
            return ir.Call(node.name, new_args)

    def transform_NamedPred(self, node):
        new_args = [self.transform(arg) for arg in node.args]
        new_restrictions = {self.transform(var): self.transform(restriction) for var, restriction in node.arg_restrictions.items()}
        return ir.NamedPred(node.name, new_args, new_restrictions, self.transform(node.body))

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
        return ir.Restriction(list(map(self.transform, node.restrict_vars)), self.transform(node.pred))

    def transform_PralineDisplay(self, node):
        return ir.PralineDisplay(self.transform(node.term))

    def transform_PralineExecute(self, node):
        return ir.PralineExecute(self.transform(node.term))

    def transform_PralineDef(self, node):
        return ir.PralineDef(self.transform(node.name), list(map(self.transform, node.args)), self.transform(node.body))

    def transform_PralineApp(self, node):
        return ir.PralineApp(self.transform(node.receiver), self.transform(node.arg))

    def transform_PralineAdd(self, node):
        return ir.PralineAdd(self.transform(node.a), self.transform(node.b))

    def transform_PralineDiv(self, node):
        return ir.PralineDiv(self.transform(node.a), self.transform(node.b))

    def transform_PralineSub(self, node):
        return ir.PralineSub(self.transform(node.a), self.transform(node.b))

    def transform_PralineMul(self, node):
        return ir.PralineMul(self.transform(node.a), self.transform(node.b))

    def transform_PralineExponent(self, node):
        return ir.PralineExponent(self.transform(node.a), self.transform(node.b))

    def transform_PralineNeg(self, node):
        return ir.PralineNeg(self.transform(node.a))

    def transform_PralineList(self, node):
        return ir.PralineList(self.transform(node.head), self.transform(node.tail))

    def transform_PralineMatch(self, node):
        return ir.PralineMatch(self.transform(node.t), list(map(self.transform, node.arms)))

    def transform_PralineMatchArm(self, node):
        return ir.PralineMatchArm(self.transform(node.pat), self.transform(node.expr))

    def transform_PralineMatchInt(self, node):
        return ir.PralineMatchInt(self.transform(node.val))

    def transform_PralineMatchString(self, node):
        return ir.PralineMatchString(self.transform(node.val))

    def transform_PralineMatchList(self, node):
        return ir.PralineMatchList(self.transform(node.head), self.transform(node.tail))

    def transform_PralineMatchVar(self, node):
        return ir.PralineMatchVar(self.transform(node.var))

    def transform_PralineIf(self, node):
        return ir.PralineIf(self.transform(node.cond), self.transform(node.e1), self.transform(node.e2))

    def transform_PralinePecanTerm(self, node):
        return ir.PralinePecanTerm(self.transform(node.pecan_term))

    def transform_PralineLambda(self, node):
        return ir.PralineLambda(list(map(self.transform, node.params)), self.transform(node.body))

    def transform_PralineLetPecan(self, node):
        return ir.PralineLetPecan(self.transform(node.var), self.transform(node.pecan_term), self.transform(node.body))

    def transform_PralineLet(self, node):
        return ir.PralineLetPecan(self.transform(node.var), self.transform(node.expr), self.transform(node.body))

    def transform_PralineTuple(self, node):
        return ir.PralineTuple(list(map(self.transform, node.vals)))

    def transform_PralineVar(self, node):
        return ir.PralineVar(node.var_name)

    def transform_PralineInt(self, node):
        return ir.PralineInt(node.val)

    def transform_PralineString(self, node):
        return ir.PralineString(node.val)

    def transform_PralineBool(self, node):
        return ir.PralineBool(node.val)

    def transform_PralineEq(self, node):
        return ir.PralineEq(self.transform(node.a), self.transform(node.b))

    def transform_PralineNe(self, node):
        return ir.PralineNe(self.transform(node.a), self.transform(node.b))

    def transform_PralineGe(self, node):
        return ir.PralineGe(self.transform(node.a), self.transform(node.b))

    def transform_PralineLe(self, node):
        return ir.PralineLe(self.transform(node.a), self.transform(node.b))

    def transform_PralineGt(self, node):
        return ir.PralineGt(self.transform(node.a), self.transform(node.b))

    def transform_PralineLt(self, node):
        return ir.PralineLt(self.transform(node.a), self.transform(node.b))

