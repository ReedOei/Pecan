#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.optimizer.basic_optimizer import BasicOptimizer
from pecan.lang.type_inference import *

from pecan.lang.ir import *

class ExpressionExtractor(IRTransformer):
    def __init__(self, prog):
        super().__init__()
        self.prog = prog

        # TODO: Explain of these and simplify if possible
        self.expressions = {}
        self.expressions_compute = {}
        self.to_compute = {}
        self.dep_graph = {}

        self.changed = False

    def dep_order(self, new_vars):
        compute_vars = []

        def add_var(new_var):
            if new_var in compute_vars:
                compute_vars.remove(new_var)
            compute_vars.append(new_var)

        for v in new_vars:
            if self.is_var(v):
                add_var(v)
                for new_var in self.dep_order(self.dep_graph[v]):
                    add_var(new_var)

        return compute_vars

    def compute_variables_for_pred(self, compute_vars, pred):
        compute_vars = self.dep_order(compute_vars)

        new_pred = pred
        for v in compute_vars:
            expr = self.to_compute[v]
            to_compute = self.expressions_compute[expr]

            # TODO: Make this cleaner
            if v.get_type() is not None and v.get_type().get_restriction() is not None:
                new_pred = Exists(v, v.get_type().restrict(v), Conjunction(Equals(to_compute, v), new_pred))
            else:
                new_pred = Exists(v, None, Conjunction(Equals(to_compute, v), new_pred))

        return new_pred

    def is_var(self, var):
        return var in self.dep_graph

    def transform_Sub(self, node):
        if node.is_int:
            return node

        if not node in self.expressions:
            self.changed = True

            new_a = self.transform(node.a)
            new_b = self.transform(node.b)

            t = node.get_type() if node.get_type() is not None else InferredType()
            new_var = VarRef(self.prog.fresh_name()).with_type(t)

            self.expressions[node] = new_var
            self.expressions_compute[node] = Sub(new_a, new_b).with_type(node.get_type())
            self.to_compute[new_var] = node
            self.dep_graph[new_var] = list(set(filter(self.is_var, [new_a, new_b])))

        return self.expressions[node]

    def transform_Add(self, node):
        if node.is_int:
            return node

        if not node in self.expressions:
            self.changed = True

            new_a = self.transform(node.a)
            new_b = self.transform(node.b)

            t = node.get_type() if node.get_type() is not None else InferredType()
            new_var = VarRef(self.prog.fresh_name()).with_type(t)

            self.expressions[node] = new_var
            self.expressions_compute[node] = Add(new_a, new_b).with_type(node.get_type())
            self.to_compute[new_var] = node
            self.dep_graph[new_var] = list(set(filter(self.is_var, [new_a, new_b])))

        return self.expressions[node]

class CSEOptimizer(BasicOptimizer):
    def __init__(self, master_optimizer):
        super().__init__(master_optimizer)

    def worth_optimization(self, node):
        if type(node) is VarRef:
            return False

        if not isinstance(node, BinaryIRExpression):
            return False

        if (type(node.a) is VarRef or type(node.a) is IntConst) and (type(node.b) is VarRef or type(node.b) is IntConst):
            return False

        return True

    def transform_Equals(self, node):
        extractor = ExpressionExtractor(self.prog)

        compute_vars = []
        if isinstance(node.a, BinaryIRExpression) and self.worth_optimization(node.a):
            aa = extractor.transform(node.a.a)
            ab = extractor.transform(node.a.b)
            compute_vars += [aa, ab]
            new_a = type(node.a)(aa, ab)
        else:
            new_a = node.a

        if isinstance(node.b, BinaryIRExpression) and self.worth_optimization(node.b):
            ba = extractor.transform(node.b.a)
            bb = extractor.transform(node.b.b)
            compute_vars += [ba, bb]
            new_b = type(node.b)(ba, bb)
        else:
            new_b = node.b

        self.changed |= extractor.changed

        return extractor.compute_variables_for_pred(compute_vars, Equals(new_a, new_b))

