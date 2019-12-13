#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from colorama import Fore, Style

import time
import os
from functools import reduce

import spot

class ASTNode:
    def __init__(self):
        self.type = None

    def transform(self, transformer):
        return NotImplementedError('Transform not implemented for {}'.format(self.__class__.__name__))

    def evaluate_node(self, prog):
        raise NotImplementedError

class Expression(ASTNode):
    def __init__(self):
        super().__init__()
        self.is_int = True

    # This should be overriden by all expressions
    def show(self):
        raise NotImplementedError

    def __repr__(self):
        if self.type is None:
            return self.show()
        else:
            return f'{self.show()} : {self.get_type()}'

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

    # The evaluate function returns an automaton representing the expression
    def evaluate_node(self, prog):
        return None # Should never be called on the base Predicate class

