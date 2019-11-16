#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from colorama import Fore, Style

import time
import os

from lark import Lark, Transformer, v_args
import spot

from pecan.tools.automaton_tools import AutomatonTransformer, Substitution

class ASTNode:
    id = 0
    def __init__(self):
        #TODO: detect used labels and avoid those
        self.label = "__pecan"+str(Expression.id)
        Expression.id += 1
        #TODO: remove this after it's done
        if prog.debug:
            print(self.label)
        pass

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

class AutLiteral(Predicate):
    def __init__(self, aut):
        super().__init__()
        self.aut = aut

    def evaluate(self, prog):
        return self.aut

    def __repr__(self):
        return 'AUTOMATON LITERAL' # TODO: Maybe improve this?

class SpotFormula(Predicate):
    def __init__(self, formula_str):
        super().__init__()
        self.formula_str = formula_str

    def evaluate(self, prog):
        return spot.translate(self.formula_str)

    def __repr__(self):
        return 'LTL({})'.format(self.formula_str)

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
        self.args = list(map(str, args))
        self.body = body

        self.body_evaluated = None

    def call(self, prog, arg_names=None):
        if self.body_evaluated is None:
            self.body_evaluated = self.body.evaluate(prog)

        if arg_names is None:
            return self.body_evaluated
        else:
            arg_names = list(map(str, arg_names))
            arg_vars = list(map(lambda name: spot.formula_ap(name), arg_names))
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
        self.quiet = False
        self.eval_level = 0
        self.result = None
        self.search_paths = []

    def evaluate(self, old_env=None):
        if old_env is not None:
            self.preds.update(old_env.preds)
            self.context = self.context + old_env.context
            self.parser = old_env.parser

        succeeded = True
        msgs = []

        for d in self.defs:
            if type(d) is NamedPred:
                self.preds[d.name] = d
            else:
                result = d.evaluate(self)
                if result is not None:
                    if result.failed():
                        succeeded = False
                        msgs.append(result.message())

        self.result = Result('\n'.join(msgs), succeeded)

        return self

    def call(self, pred_name, args=None):
        if pred_name in self.preds:
            return self.preds[pred_name].call(self, args)
        else:
            raise Exception(f'Predicate {pred_name} not found!')

    def locate_file(self, filename):
        for path in self.search_paths:
            try_path = os.path.join(path, filename)
            if os.path.exists(try_path):
                return try_path

        raise FileNotFoundError(filename)

    def __repr__(self):
        return repr(self.defs)

class Result:
    def __init__(self, msg, succeeded):
        self.msg = msg
        self.__succeeded = succeeded

    def succeeded(self):
        return self.__succeeded

    def failed(self):
        return not self.succeeded()

    def message(self):
        return self.msg

    def print_result(self):
        if self.succeeded():
            print(f'{Fore.GREEN}{self.msg}{Style.RESET_ALL}')
        else:
            print(f'{Fore.RED}{self.msg}{Style.RESET_ALL}')

class Context:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return '{}'.format(self.name)

