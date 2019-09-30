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

class Neg(Expression):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def __repr__(self):
        return '(-{})'.format(self.a)

class VarRef(Expression):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def evaluate(self, prog):
        return spot.translate(spot.formula(var_name)) # Make a simple formula for just this one variable

    def __repr__(self):
        return self.var_name

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

class Predicate(ASTNode):
    def __init__(self):
        super().__init__()

    # The evaluate function returns an automaton representing the expression
    def evaluate(self, prog):
        return None # Should never be called on the base Predicate class

class Equals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return Iff(self.a, self.b).evaluate(prog)

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class NotEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return Iff(Complement(self.a), self.b).evaluate(prog)

    def __repr__(self):
        return '({} ≠ {})'.format(self.a, self.b)

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

class Conjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return spot.product(self.a.evaluate(prog), self.b.evaluate(prog))

    def __repr__(self):
        return '({} ∧ {})'.format(self.a, self.b)

class Disjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return spot.product_or(self.a.evaluate(prog), self.b.evaluate(prog))

    def __repr__(self):
        return '({} ∨ {})'.format(self.a, self.b)

class Complement(Predicate):
    def __init__(self, a):
        super().__init__()
        self.a = a

    def evaluate(self, prog):
        return spot.complement(self.a.evaluate(prog))

    def __repr__(self):
        return '(¬{})'.format(self.a, self.b)

class Forall(Predicate):
    def __init__(self, var_name, pred):
        super().__init__()
        self.var_name = var_name
        self.pred = pred

    def __repr__(self):
        return '(∀{} ({}))'.format(self.var_name, self.pred)

class Exists(Predicate):
    def __init__(self, var_name, pred):
        super().__init__()
        self.var_name = var_name
        self.pred = pred

    def __repr__(self):
        return '(∃{} ({}))'.format(self.var_name, self.pred)

class Call(Predicate):
    def __init__(self, name, args):
        super().__init__()
        self.name = name
        self.args = args

    def __repr__(self):
        return '({}({}))'.format(self.name, ', '.join(self.args))

class Iff(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return Disjunction(Conjunction(self.a, self.b), Conjunction(Complement(self.a), Complement(self.b))).evaluate(prog)

    def __repr__(self):
        return '({} ⟺  {})'.format(self.a, self.b)

class Implies(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def evaluate(self, prog):
        return Disjunction(Complement(self.a), self.b).evaluate(prog)

    def __repr__(self):
        return '({} ⟹  {})'.format(self.a, self.b)

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

        self.preds = {}

    def evaluate(self):
        for d in defs:
            if type(d) is NamedPred:
                self.preds[d.name] = d
            else:
                d.evaluate(self)

    def __repr__(self):
        if len(self.preds) > 0:
            return '{}\n\n{}'.format('\n'.join(self.preds), self.query)
        else:
            return '{}'.format(self.query)

