#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import ast
import itertools as it

from pecan.automata.finite import FiniteAutomaton

def load_finite(filename, args):
    # Finite automata are stored by default as Python dictionaries, which makes loading them quite simple
    with open(filename, 'r') as f:
        aut = ast.literal_eval(f.read())

    aut_args = aut['var_map']
    for i, arg in enumerate(args):
        if aut_args[arg][0] != i:
            raise Exception('{} is the {}-th argument of {}, not the {}-th'.format(arg, aut_args[arg][0], filename, i))

    # Build the alphabet from the inputs if one wasn't provided.
    alphabets = [alphabet for _, (_, alphabet) in aut_args.items()]
    if not 'alphabet' in aut['aut']:
        aut['aut']['alphabet'] = set(' '.join(syms) for syms in it.product(*alphabets))

    res = FiniteAutomaton(aut['aut'], aut['var_map'])
    res.special_attr = aut.get('special_attr', None)

    return res

