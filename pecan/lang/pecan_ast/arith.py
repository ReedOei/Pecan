#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.tools.automaton_tools import Substitution, AutomatonTransformer, Projection
from pecan.lang.pecan_ast import *

class Add(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def change_label(self, label): # for changing label to __constant#
        self.label = label

    def show(self):
        # The operands should always have the same type, but in the interest of debugging, we should display when this is not the case
        if self.a.get_type() == self.b.get_type():
            return '({} + {})'.format(self.a.show(), self.b.show())
        else:
            return '({} + {})'.format(self.a, self.b)

    def transform(self, transformer):
        return transformer.transform_Add(self)

class Sub(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def __repr__(self):
        return '({} - {})'.format(self.a, self.b)

    def transform(self, transformer):
        return transformer.transform_Sub(self)

class Mul(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        if not self.a.is_int and not self.b.is_int:
            raise AutomatonArithmeticError("At least one argument of multiplication must be an constant integer in {}".format(self))
        # We assumed above that a was the int, but it might not be; if it wasn't, just swap the two
        if not self.a.is_int:
            self.a, self.b = self.b, self.a

    def transform(self, transformer):
        return transformer.transform_Mul(self)

    def show(self):
        return '({} * {})'.format(self.a, self.b)

    def evaluate_int(self, prog):
        assert self.is_int
        return self.a.evaluate_int(prog) * self.b.evaluate_int(prog)


#TODO:
class Div(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)
        if not self.is_int:
            raise NotImplementedError("Division with automaton hasn't been implemented, sorry. {}".format(self))
        if not self.b.is_int:
            raise AutomatonArithmeticError("Second argument of division must be an integer in {}".format(self))

    def show(self):
        return '({} / {})'.format(self.a, self.b)

    def transform(self, transformer):
        return transformer.transform_Div(self)

constants_map = {}
class IntConst(Expression):
    # Constant 0 is defined as 000000...
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

    def evaluate_node(self, prog):
        if self.a.is_int and self.b.is_int:
            return spot.formula('1').translate() if self.a.evaluate_int(prog) <= self.b.evaluate_int(prog) else spot.formula('0').translate()
        return Disjunction(Less(self.a,self.b),Equals(self.a,self.b)).evaluate(prog)

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

class AutomatonArithmeticError(Exception):
    pass

