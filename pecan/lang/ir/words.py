#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.ir import *

class Index(IRPredicate):
    def __init__(self, var_name, index_expr):
        super().__init__()
        self.var_name = var_name
        self.index_expr = index_expr
        self.is_int = False

    def evaluate_node(self, prog):
        return Call(self.var_name, [self.index_expr]).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_Index(self)

    def __repr__(self):
        return '{}[{}]'.format(self.var_name, self.index_expr)

class IndexRange(IRPredicate):
    def __init__(self, var_name, start, end):
        super().__init__()
        self.var_name = var_name
        self.start = start
        self.end = end

    def bounds_check(self, idx_var):
        return Less(Add(self.start, idx_var).with_type(self.start.get_type()), self.end)

    def index_expr(self, idx_var):
        return Index(self.var_name, Add(self.start, idx_var).with_type(self.start.get_type()))

    def transform(self, transformer):
        return transformer.transform_IndexRange(self)

    def __repr__(self):
        return '{}[{}..{}]'.format(self.var_name, self.start, self.end)

class EqualsCompareIndex(IRPredicate):
    def __init__(self, is_equals, index_a, index_b):
        super().__init__()
        self.is_equals = is_equals
        self.index_a = index_a
        self.index_b = index_b

    def evaluate_node(self, prog):
        base_pred = Conjunction(Disjunction(Complement(self.index_a), self.index_b), Disjunction(Complement(self.index_b), self.index_a))
        if self.is_equals:
            return base_pred.evaluate(prog)
        else:
            return Complement(base_pred).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_EqualsCompareIndex(self)

    def __repr__(self):
        if self.is_equals:
            return '{} = {}'.format(self.index_a, self.index_b)
        else:
            return '{} ≠ {}'.format(self.index_a, self.index_b)

class EqualsCompareRange(IRPredicate):
    def __init__(self, is_equals, index_a, index_b):
        super().__init__()
        self.is_equals = is_equals
        self.index_a = index_a
        self.index_b = index_b

    def evaluate_node(self, prog):
        idx_var = VarRef(prog.fresh_name())

        # We want to make sure that the two words that we are comparing are the same length;
        # Ordinarily, you'd probably use subtraction, but addition is safer because subtraction
        # on natural numbers can be very weird if we go negative
        same_range = Equals(Add(self.index_a.end, self.index_b.start).with_type(self.index_a.end.get_type()),
                            Add(self.index_b.end, self.index_a.start).with_type(self.index_a.end.get_type()))

        # bounds_checks = Conjunction(self.index_a.bounds_check(idx_var), self.index_b.bounds_check(idx_var))
        # Only do bounds check on the first index, because we've verified the bounds are the same
        bounds_checks = self.index_a.bounds_check(idx_var)
        equality_check = EqualsCompareIndex(True, self.index_a.index_expr(idx_var), self.index_b.index_expr(idx_var))
        all_equal = Complement(Exists(idx_var, Conjunction(bounds_checks, Complement(equality_check))))
        base_pred = Conjunction(same_range, all_equal)

        if self.is_equals:
            return base_pred.evaluate(prog)
        else:
            return Complement(base_pred).evaluate(prog)

    def transform(self, transformer):
        return transformer.transform_EqualsCompareRange(self)

    def __repr__(self):
        if self.is_equals:
            return '{} = {}'.format(self.index_a, self.index_b)
        else:
            return '{} ≠ {}'.format(self.index_a, self.index_b)

