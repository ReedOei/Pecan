#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.pecan_ast import *

# Below, Index and IndexRange just exist for parsing purposes, eventually we will transform these into EqualsCompare(Index|Range|Const) predicates
class Index(Predicate):
    def __init__(self, var_name, index_expr):
        super().__init__()
        self.var_name = var_name
        self.index_expr = index_expr
        self.is_int = False

    def evaluate_node(self, prog):
        return Call(self.var_name, [self.index_expr]).evaluate(prog)

    def __repr__(self):
        return '{}[{}]'.format(self.var_name, self.index_expr)

class IndexRange(Predicate):
    def __init__(self, var_name, start, end):
        super().__init__()
        self.var_name = var_name
        self.start = start
        self.end = end

    def bounds_check(self, idx_var):
        return Less(Add(self.start, idx_var), self.end)

    def index_expr(self, idx_var):
        return Index(self.var_name, Add(self.start, idx_var))

    def __repr__(self):
        return '{}[{}..{}]'.format(self.var_name, self.start, self.end)

class EqualsCompareIndex(Predicate):
    def __init__(self, is_equals, index_a, index_b):
        super().__init__()
        self.is_equals = is_equals
        self.index_a = index_a

        if type(index_b) is IntConst:
            if index_b.val == 0:
                self.index_b = FormulaTrue()
            elif index_b.val == 1:
                self.index_b = FormulaFalse()
            else:
                # TODO: Remove this restriction
                raise Exception('Automatic words can only be binary (i.e., 0 or 1), {} is not allowed (in "{} = {}")'.format(b.val, a, b))
        elif isinstance(index_b, Predicate):
            self.index_b = index_b
        else:
            raise Exception('Unexpected index expression on RHS: {} = {}'.format(index_a, const_val))

    def evaluate_node(self, prog):
        base_pred = Iff(self.index_a, self.index_b)
        if self.is_equals:
            return base_pred.evaluate(prog)
        else:
            return Complement(base_pred).evaluate(prog)

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

    def evaluate_node(self, prog):
        idx_var = VarRef(prog.fresh_name())

        # We want to make sure that the two words that we are comparing are the same length;
        # Ordinarily, you'd probably use subtraction, but addition is safer because subtraction
        # on natural numbers can be very weird if we go negative
        same_range = Equals(Add(self.index_a.end, self.index_b.start), Add(self.index_b.end, self.index_a.start))

        bounds_checks = Conjunction(self.index_a.bounds_check(idx_var), self.index_b.bounds_check(idx_var))
        equality_check = EqualsCompareIndex(True, self.index_a.index_expr(idx_var), self.index_b.index_expr(idx_var))
        all_equal = Forall(idx_var, Implies(bounds_checks, equality_check))
        base_pred = Conjunction(same_range, all_equal)

        if self.is_equals:
            return base_pred.evaluate(prog)
        else:
            return Complement(base_pred).evaluate(prog)

    def __repr__(self):
        if self.is_equals:
            return '{} = {}'.format(self.index_a, self.index_b)
        else:
            return '{} ≠ {}'.format(self.index_a, self.index_b)

