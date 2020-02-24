#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast.base import *

def process_args(app, body):
    if isinstance(app, PralineApp):
        rest_args, new_body = process_args(app.receiver, body)
        new_arg, final_body = split_arg(app.arg, new_body)
        return rest_args + [new_arg], final_body
    else:
        return [app], body

def split_arg(arg, body):
    if isinstance(arg, PralineVar):
        return arg, body
    elif isinstance(arg, PralineTuple):
        placeholder_arg = PralineVar(PralineTerm.fresh_name())
        return placeholder_arg, PralineMatch(placeholder_arg, [PralineMatchArm(arg.build_match(), body)])
    else:
        raise Exception('Unexpected term in argument position: {}'.format(arg))

class PralineTerm(ASTNode):
    var_counter = 0
    @staticmethod
    def fresh_name():
        label = "__arg{}".format(PralineTerm.var_counter)
        PralineTerm.var_counter += 1
        return label

    def __init__(self):
        super().__init__()

    def as_match(self):
        raise NotImplementedError

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
        def_params, new_body = process_args(def_id, body)

        self.name = def_params[0]
        self.args = def_params[1:]
        self.body = new_body

    def transform(self, transformer):
        return transformer.transform_PralineDef(self)

    def show(self):
        return 'Define {} {} := {} .'.format(self.name, self.args, self.body)

class PralineApp(PralineTerm):
    def __init__(self, receiver, arg):
        super().__init__()
        self.receiver = receiver
        self.arg = arg

    def transform(self, transformer):
        return transformer.transform_PralineApp(self)

    def show(self):
        return '({} {})'.format(self.receiver, self.arg)

class PralineVar(PralineTerm):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def transform(self, transformer):
        return transformer.transform_PralineVar(self)

    def build_match(self):
        return PralineMatchVar(self.var_name)

    def show(self):
        return '{}'.format(self.var_name)

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
        return transformer.transform_PralineDiv(self)

    def show(self):
        return '({} / {})'.format(self.a, self.b)

class PralineSub(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineSub(self)

    def show(self):
        return '({} - {})'.format(self.a, self.b)

class PralineMul(PralineBinaryOp):
    def __init__(self, a, b):
        super().__init__(a, b)

    def transform(self, transformer):
        return transformer.transform_PralineMul(self)

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

    def build_match(self):
        return PralineMatchList(self.head.build_match(), self.tail.build_match())

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
        return transformer.transform_PralineMatchString(self)

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

class PralineMatchTuple(PralineMatchPat):
    def __init__(self, vals):
        super().__init__()
        self.vals = vals

    def transform(self, transformer):
        return transformer.transform_PralineMatchTuple(self)

    def show(self):
        return 'PralineMatchTuple({})'.format(','.join(map(repr, self.vals)))

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
        self.params, self.body = process_args(params, body)

    def transform(self, transformer):
        return transformer.transform_PralineLambda(self)

    def show(self):
        return '(\\ {} -> {})'.format(self.params, self.body)

class PralineLetPecan(PralineTerm):
    def __init__(self, var_name, pecan_term, body):
        super().__init__()
        self.var_name = var_name
        self.pecan_term = pecan_term
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineLetPecan(self)

    def show(self):
        return '(let {} be {} in {})'.format(self.var_name, self.pecan_term, self.body)

class PralineLet(PralineTerm):
    def __init__(self, var_name, expr, body):
        super().__init__()
        self.var_name = var_name
        self.expr = expr
        self.body = body

    def transform(self, transformer):
        return transformer.transform_PralineLet(self)

    def show(self):
        return '(let {} := {} in {})'.format(self.var_name, self.expr, self.body)

class PralineTuple(PralineTerm):
    def __init__(self, vals):
        super().__init__()
        self.vals = vals

    def build_match(self):
        return PralineMatchTuple([v.build_match() for v in self.vals])

    def transform(self, transformer):
        return transformer.transform_PralineTuple(self)

    def show(self):
        return '({})'.format(','.join(map(repr, self.vals)))

class PralineInt(PralineTerm):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineInt(self)

    def build_match(self):
        return PralineMatchInt(self.val)

    def show(self):
        return 'PralineInt({})'.format(self.val)

class PralineString(PralineTerm):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineString(self)

    def build_match(self):
        return PralineMatchInt(self.val)

    def show(self):
        return 'PralineString({})'.format(self.val)

class PralineBool(PralineTerm):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def transform(self, transformer):
        return transformer.transform_PralineBool(self)

    def show(self):
        return 'PralineBool({})'.format(self.val)

class PralineDo(PralineTerm):
    def __init__(self, terms):
        super().__init__()
        self.terms = terms

    def transform(self, transformer):
        return transformer.transform_PralineDo(self)

    def show(self):
        return 'do\n    {}'.format('\n    '.join(map(repr, self.terms)))

