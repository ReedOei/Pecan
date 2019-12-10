import itertools
import string

import spot

from pecan.lang.ast import *
from pecan import program

def truth_val(prog, pred):
    evaluated = pred.evaluate(prog)
    if evaluated.is_empty(): # If we accept nothing, we are false
        return 'false'
    elif spot.complement(evaluated).is_empty(): # If our complement accepts nothing, we accept everything, so we are true
        return 'true'
    else: # Otherwise, we are neither true nor false: i.e., not all variables have been eliminated
        return 'sometimes'

def gen_vars(c):
    i = 0
    n = 0
    tot = 0

    letters = string.ascii_lowercase

    while tot < c:
        if i == 0:
            yield letters[n]
        else:
            yield '{}{}'.format(letters[n], i)

        n += 1
        if n >= 26:
            n = 0
            i += 1
        tot += 1

def gen_thms(var_count):
    prog = program.from_source('')
    return gen_preds(prog, list(gen_vars(var_count)))

def gen_pairs():
    lim = 0
    yield (0,0)
    while True:
        for i in range(lim):
            yield (lim, i)
            yield (i, lim)
        lim += 1

def gen_preds(prog, var_list):
    while True:
        for depth, expr_depth in gen_pairs():
            for pred in gen_depth(var_list, depth, expr_depth):
                for quantified in quantify(var_list, pred):
                    if truth_val(prog, quantified) == 'true':
                        yield quantified

def quantify(var_list, pred):
    if len(var_list) == 0:
        yield pred
    else:
        quants = [Exists, Forall]

        for quant in quants:
            for quantified in quantify(var_list[1:], quant(var_list[0], pred)):
                yield quantified

def gen_depth(var_list, depth, expr_depth):
    if depth == 0:
        for expr1 in gen_expr(var_list, expr_depth):
            for expr2 in gen_expr(var_list, expr_depth):
                yield Equals(expr1, expr2)
    else:
        bin_ops = [Conjunction, Disjunction]
        un_ops = [Complement]

        for unary in un_ops:
            for pred in gen_depth(var_list, depth - 1, expr_depth):
                yield unary(pred)

        for op in bin_ops:
            for pred1 in gen_depth(var_list, depth - 1, expr_depth):
                for pred2 in gen_depth(var_list, depth - 1, expr_depth):
                    yield op(pred1, pred2)

def gen_expr(var_list, expr_depth):
    if expr_depth == 0:
        for var in var_list:
            yield VarRef(var)
    else:
        bin_ops = [Add, Sub]
        for bin_op in bin_ops:
            for pred1 in gen_expr(var_list, expr_depth - 1):
                for pred2 in gen_expr(var_list, expr_depth - 1):
                    yield bin_op(pred1, pred2)

