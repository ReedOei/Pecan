#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import buddy
import math
import spot

class Transition:
    def __init__(self, input_line):
        split = input_line.split('->')
        self.inputs = [int(inp) for inp in split[0].split()]
        self.dest_state_num = int(split[1])

    # Suppose we have the following transition
    def encode(self, aut, hoa_aut, state):
        encoded_inputs = [aut.encode(inp) for inp in self.inputs]

        # zip(*xs) will transpose (basically) xs
        for i, input_chars in enumerate(zip(*encoded_inputs)):
            aut.get_state_num()

        return hoa_aut

class State:
    def __init__(self, state_num, acc):
        split = input_line.split()
        self.state_num = state_num
        self.acc = acc

        self.transitions = []

    def add_transition(self, transition):
        self.transitions.append(transition)

    def encode_transitions(self, aut, hoa_aut):
        for transition in self.transitions:
            hoa_aut = transition.encode(aut, hoa_aut, self)

        return hoa_aut

class BinaryAutomaton:
    def __init__(self, input_alphabets, formal_arg_names):
        self.input_alphabets = input_alphabets
        self.formal_arg_names = formal_arg_names

        self.max_alphabet = max(self.input_alphabets)
        self.encoding_length = math.ceil(math.log(self.max_alphabet, 2))

        self.states = []

        self.state_num = 0

        self.hoa_aut = spot.make_twa_graph()

        aps = {}
        for formal in self.formal_arg_names:
            aps[formal] = buddy.bdd_ithvar(self.hoa_aut.register_ap(formal))

        self.hoa_aut.set_buchi()
        self.hoa_aut.set_init_state(0)

        self.intermediate_states = {}

    def add_state(self, line):
        split = line.split()
        acc = int(split[1]) == 1

        state_num = self.hoa_aut.new_state()
        new_state = State(state_num, acc)
        self.states.append(state)

        return new_state

    def get_state_num(self, state, cur_inputs):
        key = (state.state_num, cur_inputs)
        if key not in self.intermediate_states:
            self.intermediate_states[key] = self.hoa_aut.new_state()

        return self.intermediate_states[key]

    def to_hoa(self):
        for state in self.states:
            self.hoa_aut = state.encode_transitions(self, self.hoa_aut)

        return self.hoa_aut

def convert_walnut(filename, inp_names):
    with open(filename, 'r') as f:
        return convert_walnut_lines(f.readlines(), inp_names)

def parse_bases(line):
    # TODO: Warn if bases aren't all the same length.
    # TODO: Keep track of encoding along with variables and throw errors if variables are used wrong.
    bases = []

    split = [base_str.strip() for base_str in line.split()]

    for base_str in split:
        # Convert something like "{0,1,2}" into [0,1,2], then count how many places there are
        # TODO: Warn if base isn't all consecutive numbers.
        if base_str[0] == '{' and base_str[-1] == '}':
            base = len([int(part) for part in base_str[1:-1].split(',')])
            bases.append(base)
        else:
            raise Exception('Improperly formatted base string (expected it to be wrapped in "{{" and "}}"): "{}"'.format(base_str))

    return bases

# TODO: It would be nice if we used a real parser for all this stuff (same for convert_hoa.py)
def convert_walnut_lines(lines, inp_names):
    cur_state = None
    aut = None

    bases = []

    for lineno, line in enumerate(lines):
        line = line.strip()

        if line[0] == '{':
            if aut is not None:
                raise Exception('Only one alphabet line is allowed!')

            # It's the alphabet line,
            bases = parse_bases(line)

            if len(bases) != len(inp_names):
                raise Exception('Got {} input alphabets but only {} formal arguments!'.format(len(bases), len(inp_names)))

            aut = BinaryAutomaton(bases, inp_names)
        elif '->' in line:
            if cur_state is None:
                raise Exception('Transition "{}" not inside any state! (line: {})'.format(line, lineno))
            cur_state.add_transition(Transition(line))
        elif len(line) > 1:
            if aut is None:
                raise Exception('Must declare the alphabet BEFORE declaring any states!')

            cur_state = aut.add_state(line)

    return aut.to_hoa()

