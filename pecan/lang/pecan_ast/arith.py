#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.pecan_ast.prog import *

class Add(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def __repr__(self):
        return '({} + {})'.format(self.a, self.b)

class Sub(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def __repr__(self):
        return '({} - {})'.format(self.a, self.b)

class Mul(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def __repr__(self):
        return '({} * {})'.format(self.a, self.b)

class Div(BinaryExpression):
    def __init__(self, a, b):
        super().__init__(a, b)

    def __repr__(self):
        return '({} / {})'.format(self.a, self.b)

class IntConst(Expression):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def __repr__(self):
        return str(self.val)

# is this something that we will want?
class Index(Expression):
    def __init__(self, var_name, index_expr):
        super().__init__()
        self.var_name = var_name
        self.index_expr = index_expr

    def __repr__(self):
        return '({}[{}])'.format(self.var_name, self.index_expr)

class Less(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} < {})'.format(self.a, self.b)

class Greater(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} > {})'.format(self.a, self.b)

class LessEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} ≤ {})'.format(self.a, self.b)

class GreaterEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} ≥ {})'.format(self.a, self.b)

