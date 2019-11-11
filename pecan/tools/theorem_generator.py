import itertools

import spot

from pecan.lang.pecan_ast import *

def truth_val(pred):
    evaluated = pred.evaluate(Program([]))
    if evaluated.is_empty(): # If we accept nothing, we are false
        return 'false'
    elif spot.complement(evaluated).is_empty(): # If our complement accepts nothing, we accept everything, so we are true
        return 'true'
    else: # Otherwise, we are neither true nor false: i.e., not all variables have been eliminated
        return 'sometimes'

def gen_preds(var_list):
    depth = 0
    while True:
        for pred in gen_depth(var_list, depth):
            for quantified in quantify(var_list, pred):
                if truth_val(quantified) == 'true':
                    yield quantified

        depth += 1

def quantify(var_list, pred):
    if len(var_list) == 0:
        yield pred
    else:
        quants = [Exists, Forall]

        for quant in quants:
            for quantified in quantify(var_list[1:], quant(var_list[0], pred)):
                yield quantified

def gen_depth(var_list, depth):
    if depth == 0:
        for x, y in itertools.combinations(var_list, 2):
            yield Equals(VarRef(x), VarRef(y))
    else:
        bin_ops = [Conjunction, Disjunction]
        un_ops = [Complement]

        for unary in un_ops:
            for pred in gen_depth(var_list, depth - 1):
                yield unary(pred)

        for op in bin_ops:
            for pred1 in gen_depth(var_list, depth - 1):
                for pred2 in gen_depth(var_list, depth - 1):
                    yield op(pred1, pred2)

