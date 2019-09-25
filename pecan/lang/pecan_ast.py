#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

class ASTNode:
    def __init__(self):
        pass

class Expression(ASTNode):
    def __init__(self):
        super().__init__()

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

    def __repr__(self):
        return self.var_name

class IntConst(Expression):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def __repr__(self):
        return str(self.val)

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

class Equals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} = {})'.format(self.a, self.b)

class NotEquals(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

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

    def __repr__(self):
        return '({} ∧ {})'.format(self.a, self.b)

class Disjunction(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

    def __repr__(self):
        return '({} ∨ {})'.format(self.a, self.b)

class Complement(Predicate):
    def __init__(self, a):
        super().__init__()
        self.a = a

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

    def __repr__(self):
        return '({} ⟺  {})'.format(self.a, self.b)

class Implies(Predicate):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

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
    def __init__(self, preds, query):
        super().__init__()
        self.preds = preds
        self.query = query

    def __repr__(self):
        if len(self.preds) > 0:
            return '{}\n\n{}'.format('\n'.join(self.preds), self.query)
        else:
            return '{}'.format(self.query)

