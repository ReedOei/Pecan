#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.ast import *

class Index(Predicate):
    def __init__(self, var_name, index_expr):
        super().__init__()
        self.var_name = var_name
        self.index_expr = index_expr
        self.is_int = False

    def transform(self, transformer):
        return transformer.transform_Index(self)

    def __repr__(self):
        return '{}[{}]'.format(self.var_name, self.index_expr)

class IndexRange(Predicate):
    def __init__(self, var_name, start, end):
        super().__init__()
        self.var_name = var_name
        self.start = start
        self.end = end

    def transform(self, transformer):
        return transformer.transform_IndexRange(self)

    def __repr__(self):
        return '{}[{}..{}]'.format(self.var_name, self.start, self.end)

class EqualsCompareIndex(Predicate):
    def __init__(self, is_equals, index_a, index_b):
        super().__init__()
        self.is_equals = is_equals
        self.index_a = index_a

        if type(index_b) is IntConst:
            if index_b.val == 0:
                self.index_b = BoolConst(False)
            elif index_b.val == 1:
                self.index_b = BoolConst(True)
            else:
                # TODO: Remove this restriction
                raise Exception('Automatic words can only be binary (i.e., 0 or 1), {} is not allowed (in "{} = {}")'.format(b.val, a, b))
        elif isinstance(index_b, Predicate):
            self.index_b = index_b
        else:
            raise Exception('Unexpected index expression on RHS: {} = {}'.format(index_a, index_b))

    def transform(self, transformer):
        return transformer.transform_EqualsCompareIndex(self)

    def __repr__(self):
        if self.is_equals:
            return '{} = {}'.format(self.index_a, self.index_b)
        else:
            return '{} ≠ {}'.format(self.index_a, self.index_b)

class EqualsCompareRange(Predicate):
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

