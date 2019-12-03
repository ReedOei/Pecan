#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from colorama import Fore, Style

import time
import os
from functools import reduce

from lark import Lark, Transformer, v_args
import spot

class ASTNode:
    id = 0
    def __init__(self):
        #TODO: detect used labels and avoid those
        self.label = "__pecan{}".format(Expression.id)
        Expression.id += 1

    def evaluate(self, prog):
        prog.eval_level += 1
        if prog.debug:
            start_time = time.time()
        result = self.evaluate_node(prog)
        prog.eval_level -= 1
        if prog.debug:
            end_time = time.time()
            print('{}{} has {} states and {} edges ({:.2f} seconds)'.format(' ' * prog.eval_level, self, result.num_states(), result.num_edges(), end_time - start_time))

        return result

    def transform(self, transformer):
        return NotImplementedError('Transform not implemented for {}'.format(self.__class__.__name__))

class Expression(ASTNode):
    def __init__(self):
        super().__init__()
        self.is_int = True
        self.type = None

    def with_type(self, new_type):
        self.type = new_type
        return self

    def get_type(self):
        return self.type

    def evaluate_node(self, prog):
        return None

class UnaryExpression(Expression):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def with_type(self, new_type):
        self.a = self.a.with_type(new_type)
        return super().with_type(new_type)

class BinaryExpression(Expression):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b
        self.is_int = a.is_int and b.is_int

    def with_type(self, new_type):
        self.a = self.a.with_type(new_type)
        self.b = self.b.with_type(new_type)
        return super().with_type(new_type)

class Predicate(ASTNode):
    def __init__(self):
        super().__init__()

    # The evaluate function returns an automaton representing the expression
    def evaluate_node(self, prog):
        return None # Should never be called on the base Predicate class

