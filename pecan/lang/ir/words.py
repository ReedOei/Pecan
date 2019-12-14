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

    def transform(self, transformer):
        return transformer.transform_EqualsCompareIndex(self)

    def evaluate_node(self, prog):
        a_aut = self.index_a.evaluate(prog)
        b_aut = self.index_b.evaluate(prog)

        if self.is_equals:
            a_impl_b = spot.product_or(spot.complement(a_aut), b_aut)
            b_impl_a = spot.product_or(spot.complement(b_aut), a_aut)
            return spot.product(a_impl_b, b_impl_a)
        else:
            a_not_impl_b = spot.product(a_aut, spot.complement(b_aut))
            b_not_impl_a = spot.product(b_aut, spot.complement(a_aut))
            return spot.product_or(a_not_impl_b, b_not_impl_a)

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

    def transform(self, transformer):
        return transformer.transform_EqualsCompareRange(self)

    def __repr__(self):
        if self.is_equals:
            return '{} = {}'.format(self.index_a, self.index_b)
        else:
            return '{} ≠ {}'.format(self.index_a, self.index_b)

