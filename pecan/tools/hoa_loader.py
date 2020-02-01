#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.automata.buchi import BuchiAutomaton

def load_hoa(path):
    return BuchiAutomaton(spot.automaton(path))

