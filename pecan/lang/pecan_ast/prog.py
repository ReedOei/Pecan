#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

class ASTNode:
    def __init__(self):
        pass

class Expression(ASTNode):
    def __init__(self):
        super().__init__()

    def evaluate(self, prog):
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
        return spot.translate(spot.formula(self.var_name)) # Make a simple formula for just this one variable

    def __repr__(self):
        return self.var_name

class Predicate(ASTNode):
    def __init__(self):
        super().__init__()

    # The evaluate function returns an automaton representing the expression
    def evaluate(self, prog):
        return None # Should never be called on the base Predicate class

class Call(Predicate):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def __repr__(self):
        return '({}({}))'.format(self.name, ', '.join(self.args))

class NamedPred(ASTNode):
    def __init__(self, name, args, body):
        super().__init__()
        self.name = name
        self.args = args
        self.body = body

    def __repr__(self):
        return '{}({}) := {}'.format(self.name, ', '.join(self.args), self.body)

class Program(ASTNode):
    def __init__(self, defs):
        super().__init__()

        self.defs = defs
        self.preds = {}

    def evaluate(self, old_env=None):
        if old_env is not None:
            self.preds.update(old_env.preds)

        for d in self.defs:
            if type(d) is NamedPred:
                self.preds[d.name] = d
            else:
                d.evaluate(self)

        return self

    def __repr__(self):
        return repr(self.defs)

class Directive(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return '#{}'.format(self.name)

class DirectiveSave(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def evaluate(self, prog):
        prog.preds[self.pred_name].body.evaluate(prog).save(self.filename)
        return None

    def __repr__(self):
        return '#save({}) {}'.format(self.filename, self.pred_name)

