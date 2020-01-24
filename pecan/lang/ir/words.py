#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir import *

class IndexRange(IRPredicate):
    def __init__(self, var_name, start, end):
        super().__init__()
        self.var_name = var_name
        self.start = start
        self.end = end

    def bounds_check(self, idx_var):
        return Less(Add(self.start, idx_var).with_type(self.start.get_type()), self.end)

    def index_expr(self, idx_var):
        return Call(self.var_name, [Add(self.start, idx_var).with_type(self.start.get_type())])

    def transform(self, transformer):
        return transformer.transform_IndexRange(self)

    def __repr__(self):
        return '{}[{}..{}]'.format(self.var_name, self.start, self.end)

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

