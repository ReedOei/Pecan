#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast.base import *

def app_to_list(app):
    if type(app) is PralineApp:
        return app_to_list(app.receiver) + [app.arg]
    else:
        return [app]

class PralineTerm(ASTNode):
    def __init__(self):
        super().__init__()

class PralineDisplay(ASTNode):
    def __init__(self, term):
        super().__init__()
        self.term = term

    def transform(self, transformer):
        return transformer.transform_PralineDisplay(self)

    def show(self):
        return 'Display {} .'.format(self.term)

class PralineExecute(ASTNode):
    def __init__(self, term):
        super().__init__()
        self.term = term

    def transform(self, transformer):
        return transformer.transform_PralineExecute(self)

    def show(self):
        return 'Execute {} .'.format(self.term)

class PralineDef(ASTNode):
    def __init__(self, def_id, body):
        def_params = app_to_list(def_id)
        self.name = def_params[0]
        self.args = def_params[1:]
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineDef(self)

    def show(self):
        return 'Definition {} {} := {} .'.format(self.name, self.args, self.body)

class PralineCompose(PralineTerm):
    def __init__(self, f, g):
        super().__init__()
        self.f = f
        self.g = g

    def transform(self, transformer):
        return transformer.transform_PralineCompose(self)

    def show(self):
        return '({} ∘ {})'.format(self.f, self.g)

class PralineApp(PralineTerm):
    def __init__(self, receiver, arg):
        super().__init__()
        self.receiver = receiver
        self.arg = arg

    def transform(self, transformer):
        return transformer.transform_PralineApp(self)

    def show(self):
        return '({} {})'.format(self.receiver, self.arg)

class PralineBinaryOp(PralineTerm):
    def __init__(self, a, b):
        super().__init__()
        self.a = a
        self.b = b

class PralineAdd(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineAdd(self)

    def show(self):
        return '({} + {})'.format(self.a, self.b)

class PralineDiv(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineAdd(self)

    def show(self):
        return '({} / {})'.format(self.a, self.b)

class PralineSub(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineAdd(self)

    def show(self):
        return '({} - {})'.format(self.a, self.b)

class PralineMul(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineAdd(self)

    def show(self):
        return '({} * {})'.format(self.a, self.b)

class PralineExponent(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineExponent(self)

    def show(self):
        return '({} ^ {})'.format(self.a, self.b)

class PralineUnaryOp(PralineTerm):
    def __init__(self, a):
        super().__init__()
        self.a = a

class PralineNeg(PralineUnaryOp):
    def __init__(self, a):
        super().__init__(a)

    def transform(self, transformer):
        return transformer.transform_PralineNeg(self)

    def show(self):
        return '(-{})'.format(self.a)

class PralineList(PralineTerm):
    def __init__(self, head, tail):
        super().__init__()
        self.head = head
        self.tail = tail

    def transform(self, transformer):
        return transformer.transform_PralineList(self)

    def show(self):
        if self.head is None:
            return '[]'
        else:
            return '({} :: {})'.format(self.head, self.tail)

class PralineMatch(PralineTerm):
    def __init__(self, t, arms):
        super().__init__()
        self.t = t
        self.arms = arms

    def transform(self, transformer):
        return transformer.transform_PralineMatch(self)

    def show(self):
        return 'match {} with\n{}\nend'.format(self.t, '\n'.join(map(repr, self.arms)))

class PralineMatchArm(ASTNode):
    def __init__(self, pat, expr):
        super().__init__()
        self.pat = pat
        self.expr = expr

    def transform(self, transformer):
        return transformer.transform_PralineMatchArm(self)

    def show(self):
        return 'case {} => {}'.format(self.pat, self.expr)

class PralineMatchPat(ASTNode):
    def __init__(self):
        super().__init__()

class PralineMatchInt(PralineMatchPat):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineMatchInt(self)

    def show(self):
        return 'PralineMatchInt({})'.format(self.val)

class PralineMatchString(PralineMatchPat):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineMatchInt(self)

    def show(self):
        return 'PralineMatchString({})'.format(self.val)

class PralineMatchList(PralineMatchPat):
    def __init__(self, head, tail):
        super().__init__()
        self.head = head
        self.tail = tail

    def transform(self, transformer):
        return transformer.transform_PralineMatchList(self)

    def show(self):
        return 'PralineMatchList({}, {})'.format(self.head, self.tail)

class PralineMatchVar(PralineMatchPat):
    def __init__(self, var):
        super().__init__()
        self.var = var

    def transform(self, transformer):
        return transformer.transform_PralineMatchVar(self)

    def show(self):
        return '{}'.format(self.var)

class PralineIf(PralineTerm):
    def __init__(self, cond, e1, e2):
        super().__init__()
        self.cond = cond
        self.e1 = e1
        self.e2 = e2

    def transform(self, transformer):
        return transformer.transform_PralineIf(self)

    def show(self):
        return '(if {} then {} else {})'.format(self.cond, self.e1, self.e2)

class PralinePecanTerm(PralineTerm):
    def __init__(self, pecan_term):
        super().__init__()
        self.pecan_term = pecan_term

    def transform(self, transformer):
        return transformer.transform_PralinePecanTerm(self)

    def show(self):
        return '{{ {} }}'.format(self.pecan_term)

class PralineLambda(PralineTerm):
    def __init__(self, params, body):
        super().__init__()
        self.params = app_to_list(params)
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineLambda(self)

    def show(self):
        return '(\\ {} -> {})'.format(self.params, self.body)

