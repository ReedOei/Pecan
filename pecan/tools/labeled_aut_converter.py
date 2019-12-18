#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.tools.convert_hoa import convert_aut_lines

class Transition:
    def __init__(self, input_line):
        split = input_line.split('->')
        self.inputs = [inp.strip() for inp in split[0].split()]
        self.dest_label = split[1].strip()

    def to_str(self, state_map):
        return '{} -> {}'.format(self.input_str(), state_map[self.dest_label])

    def input_str(self):
        return ' '.join(self.inputs)

class State:
    def __init__(self, idx, input_line):
        self.idx = idx

        split = input_line.split(':')
        self.label = split[0].strip()
        self.acc = int(split[1]) == 1

        self.transitions = []

    def add_transition(self, transition):
        self.transitions.append(transition)

    def to_str(self, state_map):
        lines = []
        lines.append('{} {}'.format(self.idx, 1 if self.acc else 0))
        for transition in self.transitions:
            lines.append(transition.to_str(state_map))
        return lines

# TODO: It would be nice if we used a real parser for all this stuff (same for convert_hoa.py)
def convert_labeled_aut(filename, input_names):
    lines = []

    state_idx = 0
    cur_state = None

    state_map = {}
    states = []

    with open(filename, 'r') as f:
        for lineno, line in enumerate(f.readlines()):
            line = line.strip()

            if line.startswith('//') or len(line) <= 0:
                pass
            elif line[0] == '{':
                # It's the alphabet line,
                lines.append(line)
            elif '->' in line:
                if cur_state is None:
                    raise Exception('Transition "{}" not inside any state! (line: {})'.format(line, lineno))
                cur_state.add_transition(Transition(line))
            elif len(line) > 1:
                cur_state = State(state_idx, line)
                state_map[cur_state.label] = state_idx
                states.append(cur_state)
                state_idx += 1

    for state in states:
        lines.extend(state.to_str(state_map))

    return convert_aut_lines(lines, input_names)

