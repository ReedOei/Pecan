#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from colorama import Fore, Style

import time
import os
from functools import reduce

import spot

class ASTNode:
    def __init__(self):
        self.is_int = False

    def transform(self, transformer):
        return NotImplementedError('Transform not implemented for {}'.format(self.__class__.__name__))

    def evaluate_node(self, prog):
        raise NotImplementedError

    def __repr__(self):
        return self.show()

class Expression(ASTNode):
    def __init__(self):
        super().__init__()
        self.is_int = True

    # This should be overriden by all expressions
    def show(self):
        raise NotImplementedError

class UnaryExpression(Expression):
    def __init__(self, a):
        super().__init__()
        self.a = a

class BinaryExpression(Expression):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b
        self.is_int = a.is_int and b.is_int

class Predicate(ASTNode):
    def __init__(self):
        super().__init__()

class TypeHint(ASTNode):
    def __init__(self, expr_a, expr_b, body):
        super().__init__()
        self.expr_a = expr_a
        self.expr_b = expr_b
        self.body = body

    def transform(self, transformer):
        return transformer.transform_TypeHint(self)

    def __repr__(self):
        return '(typ({}) = typ({}) in {})'.format(self.expr_a, self.expr_b, self.body)

