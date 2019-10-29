#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from lark import Lark, Transformer, v_args

class ASTNode:
    def __init__(self):
        pass

    def evaluate(self, prog):
        prog.eval_level += 1
        result = self.evaluate_node(prog)
        prog.eval_level -= 1
        if prog.debug:
            print('{}{} has {} states and {} edges'.format('  ' * prog.eval_level, self, result.num_states(), result.num_edges()))

        return result

class Expression(ASTNode):
    def __init__(self):
        super().__init__()

    def evaluate_node(self, prog):
        return None

class BinaryExpression(ASTNode):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

class VarRef(Expression):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def evaluate(self, prog):
        # The automata accepts everything (because this isn't a predicate)
        return (spot.formula('1').translate(), self.var_name)

    def __repr__(self):
        return self.var_name

class Predicate(ASTNode):
    def __init__(self):
        super().__init__()

    # The evaluate function returns an automaton representing the expression
    def evaluate_node(self, prog):
        return None # Should never be called on the base Predicate class

class Call(Predicate):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def evaluate(self, prog):
        return prog.call(self.name, self.args)

    def __repr__(self):
        return '({}({}))'.format(self.name, ', '.join(self.args))

class NamedPred(ASTNode):
    def __init__(self, name, args, body):
        super().__init__()
        self.name = name
        self.args = args
        self.body = body

        self.body_evaluated = None

    def call(self, prog, arg_names=None):
        if self.body_evaluated is None:
            self.body_evaluated = self.body.evaluate(prog)

        if arg_names is None:
            return self.body_evaluated
        else:
            arg_vars = map(lambda name: spot.formula_ap(name), arg_names)
            substitution = Substitution(dict(zip(self.args, arg_vars)))
            return AutomatonTransformer(self.body_evaluated, substitution.substitute).transform()

    def __repr__(self):
        return '{}({}) := {}'.format(self.name, ', '.join(self.args), self.body)

class Program(ASTNode):
    def __init__(self, defs):
        super().__init__()

        self.defs = defs
        self.preds = {}
        self.context = []
        self.parser = None # This will be "filled in" in the main.py after we load a program
        self.debug = False
        self.eval_level = 0

    def evaluate(self, old_env=None):
        if old_env is not None:
            self.preds.update(old_env.preds)
            self.context = self.context + old_env.context
            self.parser = old_env.parser

        for d in self.defs:
            if type(d) is NamedPred:
                self.preds[d.name] = d
            else:
                d.evaluate(self)

        return self

    def call(self, pred_name, args=None):
        if pred_name in self.preds:
            return self.preds[pred_name].call(self, args)
        else:
            raise Exception(f'Predicate {pred_name} not found!')

    def __repr__(self):
        return repr(self.defs)

class Context:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return '{}'.format(self.name)

