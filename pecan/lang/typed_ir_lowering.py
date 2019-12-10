#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.ir import *

from pecan.tools.automaton_tools import TruthValue

# This class performs a number of simplifications on the IR representation, eliminating constructs that we need to know the type of to eliminate
class TypedIRLowering(IRTransformer):
    def __init__(self):
        super().__init__()

    def transform_Index(self, node):
        return Call(node.var_name, [node.index_expr])

    def transform_EqualsCompareIndex(self, node):
        new_a = self.transform(node.index_a)
        new_b = self.transform(node.index_b)
        base_pred = Conjunction(Disjunction(Complement(new_a), new_b), Disjunction(Complement(new_b), new_a))
        if node.is_equals:
            return base_pred
        else:
            return Complement(base_pred)

    def transform_EqualsCompareRange(self, node):
        idx_var = VarRef(self.current_program.fresh_name()).with_type(node.index_a.start.get_type())

        # We want to make sure that the two words that we are comparing are the same length;
        # Ordinarily, you'd probably use subtraction, but addition is safer because subtraction
        # on natural numbers can be very weird if we go negative
        same_range = Equals(Add(node.index_a.end, node.index_b.start).with_type(node.index_a.end.get_type()),
                            Add(node.index_b.end, node.index_a.start).with_type(node.index_a.end.get_type()))

        # bounds_checks = Conjunction(self.index_a.bounds_check(idx_var), self.index_b.bounds_check(idx_var))
        # Only do bounds check on the first index, because we've verified the bounds are the same
        bounds_checks = node.index_a.bounds_check(idx_var)
        equality_check = self.transform(EqualsCompareIndex(True, node.index_a.index_expr(idx_var), node.index_b.index_expr(idx_var)))
        all_equal = Complement(Exists(idx_var, Conjunction(bounds_checks, Complement(equality_check))))
        base_pred = Conjunction(same_range, all_equal)

        if node.is_equals:
            return base_pred
        else:
            return Complement(base_pred)

