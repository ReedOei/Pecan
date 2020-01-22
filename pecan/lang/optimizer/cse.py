#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.optimizer.basic_optimizer import BasicOptimizer
from pecan.lang.optimizer.tools import *
from pecan.lang.type_inference import *

from pecan.lang.ir import *

class ExpressionExtractor(IRTransformer):
    def __init__(self, scope, prog, expr_frequency, depth_threshold=None, frequency_threshold=None):
        super().__init__()
        self.scope = scope
        self.prog = prog
        self.expr_frequency = expr_frequency

        # Default is every occurrence of every expression gets extracted
        self.depth_threshold = depth_threshold or 0
        self.frequency_threshold = frequency_threshold or 0

        # TODO: Explain each of these and simplify if possible
        self.expressions = {}
        self.expressions_compute = {}
        self.to_compute = {}
        self.dep_graph = {}

        self.changed = False

    def merge(self, other):
        self.expressions.update(other.expressions)
        self.expressions_compute.update(other.expressions_compute)
        self.to_compute.update(other.to_compute)
        self.dep_graph.update(other.dep_graph)

        self.changed |= other.changed

        return self

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

    def compute_vars_for(self, pred):
        compute_vars = self.dep_order(list(self.dep_graph.keys()))

        done = set()

        new_pred = pred
        for v in compute_vars:
            expr = self.to_compute[v]
            to_compute = self.expressions_compute[expr]

            if type(to_compute) is VarRef:
                new_pred = NodeSubstitution({v: to_compute}).transform(new_pred)
            else:
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

        if self.expr_frequency.get(node, 1) >= self.frequency_threshold:
            depth = DepthAnalyzer().count(node)
            if depth < self.depth_threshold:
                return node

            if not VariableUsage().analyze(node).issubset(self.scope):
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
        else:
            new_a = self.transform(node.a)
            new_b = self.transform(node.b)
            return Sub(new_a, new_b).with_type(node.get_type())

    def transform_Add(self, node):
        if node.is_int:
            return node

        if self.expr_frequency.get(node, 1) >= self.frequency_threshold:
            depth = DepthAnalyzer().count(node)
            if depth < self.depth_threshold:
                return node

            if not VariableUsage().analyze(node).issubset(self.scope):
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
        else:
            new_a = self.transform(node.a)
            new_b = self.transform(node.b)
            return Add(new_a, new_b).with_type(node.get_type())

class CSEOptimizer(BasicOptimizer):
    def __init__(self, master_optimizer):
        super().__init__(master_optimizer)
        self.frequency = None
        self.frequency_threshold = 2

    def worth_optimization(self, node):
        if type(node) is VarRef:
            return False

        if not isinstance(node, BinaryIRExpression):
            return False

        if (type(node.a) is VarRef or type(node.a) is IntConst) and (type(node.b) is VarRef or type(node.b) is IntConst):
            return False

        return True

    def transform_Equals(self, node):
        # frequency = ExpressionFrequency().count(node)
        extractor = ExpressionExtractor(self.current_scope, self.prog, {})

        if isinstance(node.a, BinaryIRExpression) and self.worth_optimization(node.a):
            aa = extractor.transform(node.a.a)
            ab = extractor.transform(node.a.b)
            new_a = type(node.a)(aa, ab).with_type(node.a.get_type())
        else:
            new_a = node.a

        if isinstance(node.b, BinaryIRExpression) and self.worth_optimization(node.b):
            ba = extractor.transform(node.b.a)
            bb = extractor.transform(node.b.b)
            new_b = type(node.b)(ba, bb).with_type(node.b.get_type())
        else:
            new_b = node.b

        self.changed |= extractor.changed

        return extractor.compute_vars_for(Equals(new_a, new_b))

    def multipass_cse(self, extractors, node):
        new_node = node
        for extractor in extractors:
            new_node = extractor.transform(new_node)
            if type(new_node) is VarRef:
                break

        return new_node

    def pre_optimize(self, node):
        self.current_scope = {arg.var_name for arg in self.pred.args}

    def transform(self, node):
        node = super().transform(node)
        if isinstance(node, IRPredicate):
            frequency = ExpressionFrequency().count(node)

            # Extract everything that's either at least 2 levels deep or appears at least twice
            freq_extractor = ExpressionExtractor(self.current_scope, self.prog, frequency, frequency_threshold=2)

            new_node = self.multipass_cse([freq_extractor], node)

            self.changed |= freq_extractor.changed

            return freq_extractor.compute_vars_for(new_node)
        else:
            return node

    def transform_EqualsCompareIndex(self, node):
        frequency = ExpressionFrequency().count(node)

        # Extract everything that's either at least 2 levels deep or appears at least twice
        freq_extractor = ExpressionExtractor(self.current_scope, self.prog, frequency, frequency_threshold=2)
        depth_extractor = ExpressionExtractor(self.current_scope, self.prog, frequency, depth_threshold=1)

        index_a = self.multipass_cse([freq_extractor, depth_extractor], node.index_a)
        index_b = self.multipass_cse([freq_extractor, depth_extractor], node.index_b)

        self.changed |= depth_extractor.changed or freq_extractor.changed

        return depth_extractor.merge(freq_extractor).compute_vars_for(EqualsCompareIndex(node.is_equals, index_a, index_b))

    def transform_Exists(self, node: Exists):
        self.current_scope.add(node.var.var_name)
        res = super().transform_Exists(node)
        self.current_scope.remove(node.var.var_name)
        return res

