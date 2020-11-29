#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.ast import *

class Add(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def change_label(self, label): # for changing label to __constant#
        self.label = label

    def show(self):
        return '({} + {})'.format(self.a.show(), self.b.show())

    def transform(self, transformer):
        return transformer.transform_Add(self)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) + self.b.evaluate_int(prog)

class Sub(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def show(self):
        return '({} - {})'.format(self.a, self.b)

    def transform(self, transformer):
        return transformer.transform_Sub(self)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) - self.b.evaluate_int(prog)

class Mul(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_Mul(self)

    def show(self):
        return '({} * {})'.format(self.a, self.b)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) * self.b.evaluate_int(prog)

class Div(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        if not self.b.is_int:
            raise AutomatonArithmeticError("Second argument of division must be an integer in {}".format(self))

    def show(self):
        return '({} / {})'.format(self.a, self.b)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) // self.b.evaluate_int(prog)

    def transform(self, transformer):
        return transformer.transform_Div(self)

class IntConst(Expression):
    def __init__(self, val):
        super().__init__()
        self.val = val
        self.label = "__constant{}".format(self.val)

    def transform(self, transformer):
        return transformer.transform_IntConst(self)

    def evaluate_int(self, prog):
        return self.val

    def show(self):
        return str(self.val)

class Equals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_Equals(self)

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class NotEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_NotEquals(self)

    def __repr__(self):
        return '({} ≠ {})'.format(self.a, self.b)

class Less(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_Less(self)

    def __repr__(self):
        return '({} < {})'.format(self.a, self.b)

class Greater(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_Greater(self)

    def __repr__(self):
        return '({} > {})'.format(self.a, self.b)

class LessEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_LessEquals(self)

    def __repr__(self):
        return '({} ≤ {})'.format(self.a, self.b)

class GreaterEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def transform(self, transformer):
        return transformer.transform_GreaterEquals(self)

    def __repr__(self):
        return '({} ≥ {})'.format(self.a, self.b)

class Neg(UnaryExpression): # Should this be allowed?
    def __init__(self, a):
        super().__init__(a)
        self.a = a

    def transform(self, transformer):
        return transformer.transform_Neg(self)

    def show(self):
        return '(-{})'.format(self.a)

    def evaluate_int(self, prog):
        assert self.is_int
        return -self.a.evaluate_int(prog)

class PredicateExpr(Expression):
    def __init__(self, var_name, pred):
        super().__init__()
        self.var_name = var_name
        self.pred = pred

    def transform(self, transformer):
        return transformer.transform_PredicateExpr(self)

    def show(self):
        return 'Expr({}, {})'.format(self.var_name, self.pred)

class AutomatonArithmeticError(Exception):
    pass

