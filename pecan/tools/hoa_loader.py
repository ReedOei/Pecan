#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.automata.buchi import BuchiAutomaton

def from_spot_aut(base_aut):
    # In this case, we have no information about the encoding, so we just assume that each variable maps 1-1 in the HOA file specified.
    var_map = {}

    for ap in base_aut.ap():
        var_map[ap.ap_name()] = [ap.ap_name()]

    return BuchiAutomaton(base_aut, var_map)

def load_hoa(path):
    base_aut = spot.automaton(path)

    return from_spot_aut(spot.automaton(path))

