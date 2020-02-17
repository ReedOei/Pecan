#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import buddy
import math
import spot

from pecan.automata.buchi import BuchiAutomaton
from pecan.utility import VarMap

class Transition:
    def __init__(self, input_line):
        split = input_line.split('->')
        # Something like [1,2,3], representing a transition from (1,2,3) -> dest_state_num
        self.inputs = [int(inp) for inp in split[0].split()]
        self.dest_state_num = int(split[1])

    # Suppose we have the following transition
    def encode(self, aut, hoa_aut, state):
        cond = buddy.bddtrue

        for encoded_input, aps in aut.encode(self.inputs):

            for c, ap in zip(encoded_input, aps):
                if c == '0':
                    cond &= -ap
                else:
                    cond &= ap

            acc_sets = aut.acc_for(self.dest_state_num)

        if acc_sets:
            hoa_aut.new_edge(state.state_num, self.dest_state_num, cond, acc_sets)
        else:
            hoa_aut.new_edge(state.state_num, self.dest_state_num, cond)

        return hoa_aut

class State:
    def __init__(self, state_num, acc):
        self.state_num = state_num
        self.acc = acc

        self.transitions = []

    def add_transition(self, transition):
        self.transitions.append(transition)

    def encode_transitions(self, aut, hoa_aut):
        for transition in self.transitions:
            hoa_aut = transition.encode(aut, hoa_aut, self)

        return hoa_aut

    def get_acc(self):
        return [0] if self.acc else []

def base_len(base):
    return math.ceil(math.log(base, 2))

class BinaryAutomaton:
    def __init__(self, input_alphabets, formal_arg_names):
        self.input_alphabets = input_alphabets
        self.formal_arg_names = formal_arg_names

        if len(self.input_alphabets) != len(self.formal_arg_names):
            raise Exception('Number of inputs must match number of formal arguments ({} vs {})'.format(self.input_alphabets, self.formal_arg_names))

        self.states = []
        self.state_num_map = {}
        self.state_name_map = {}

        self.state_num = 0

        self.hoa_aut = spot.make_twa_graph()

        self.var_map = VarMap()
        self.bdds = {}
        for formal, base in zip(self.formal_arg_names, self.input_alphabets):
            self.var_map[formal] = [ BuchiAutomaton.fresh_ap() for _ in range(base_len(base)) ]
            self.bdds[formal] = [ buddy.bdd_ithvar(self.hoa_aut.register_ap(ap)) for ap in self.var_map[formal] ]

        self.hoa_aut.set_buchi()

    def add_state(self, line):
        split = line.split()
        state_name = int(split[0])
        acc = int(split[1]) == 1

        state_num = self.hoa_aut.new_state()

        # If it's the first state, it's going to be our initial state
        if not self.states:
            self.hoa_aut.set_init_state(state_num)

        new_state = State(state_num, acc)
        self.states.append(new_state)

        self.state_num_map[state_num] = new_state
        self.state_name_map[state_name] = state_num

        return new_state

    def encode(self, inp):
        for base, formal, sym in zip(self.input_alphabets, self.formal_arg_names, inp):
            yield bin(sym)[2:].rjust(base_len(base), '0'), self.bdds[formal]

    def acc_for(self, state_name):
        return self.state_num_map[self.state_name_map[state_name]].get_acc()

    def to_buchi(self):
        for state in self.states:
            self.hoa_aut = state.encode_transitions(self, self.hoa_aut)

        return BuchiAutomaton(self.hoa_aut, self.var_map)

def convert_walnut(filename, inp_names):
    with open(filename, 'r') as f:
        return convert_walnut_lines(f.readlines(), inp_names)

def parse_bases(line):
    # TODO: Keep track of encoding along with variables and throw errors if variables are used wrong.
    bases = []

    split = [base_str.strip() for base_str in line.split('}') if base_str.strip() != '']

    for base_str in split:
        # Convert something like "{0,1,2}" into [0,1,2], then count how many places there are
        # TODO: Warn if base isn't all consecutive numbers.
        if base_str[0] == '{':
            base = len([int(part) for part in base_str[1:].split(',')])
            bases.append(base)
        else:
            raise Exception('Improperly formatted base string (expected it to be wrapped in "{{" and "}}"): "{}"'.format(base_str))

    return bases

def convert_aut(txt, inp_names=None):
    with open(txt, 'r') as f:
        return convert_walnut_lines(f.readlines(), inp_names)

# TODO: It would be nice if we used a real parser for all this stuff
def convert_walnut_lines(lines, inp_names):
    cur_state = None
    aut = None

    bases = []

    for lineno, line in enumerate(lines):
        line = line.strip()

        if line == '':
            continue
        elif line[0] == '{':
            if aut is not None:
                raise Exception('Only one alphabet line is allowed!')

            # It's the alphabet line,
            bases = parse_bases(line)

            if len(bases) != len(inp_names):
                raise Exception('Got {} input alphabets but {} formal arguments!'.format(len(bases), len(inp_names)))

            aut = BinaryAutomaton(bases, inp_names)
        elif '->' in line:
            if cur_state is None:
                raise Exception('Transition "{}" not inside any state! (line: {})'.format(line, lineno))
            cur_state.add_transition(Transition(line))
        elif len(line) > 1:
            if aut is None:
                raise Exception('Must declare the alphabet BEFORE declaring any states!')

            cur_state = aut.add_state(line)

    return aut.to_buchi()

