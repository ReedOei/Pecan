#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import ast

import spot

from pecan.automata.buchi import BuchiAutomaton
from pecan.utility import VarMap

def from_spot_aut(base_aut):
    # In this case, we have no information about the encoding, so we just assume that each variable maps 1-1 in the HOA file specified.
    var_map = VarMap()

    for ap in base_aut.ap():
        var_map[ap.ap_name()] = [ap.ap_name()]

    return BuchiAutomaton(base_aut, var_map)

def load_hoa(path):
    with open(path, 'r') as f:
        lines = f.readlines()

    try:
        if lines[0].startswith('VAR_MAP: '):
            idx = lines[0].index(':')
            var_map_str = lines[0][idx + 1:].strip()
            var_map = ast.literal_eval(var_map_str)

            for k, vs in var_map.items():
                for v in vs:
                    BuchiAutomaton.update_counter(v)

            return BuchiAutomaton(spot.automaton('\n'.join(lines[1:])), var_map)
    except ValueError:
        pass

    return from_spot_aut(spot.automaton('\n'.join(lines)))

