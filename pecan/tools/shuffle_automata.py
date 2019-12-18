#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import buddy
import spot

class ShuffleAutomata:
    def __init__(self, aut_a, aut_b):
        if aut_a.is_sba():
            self.aut_a = aut_a
        else:
            self.aut_a = aut_a.postprocess('BA')

        if aut_b.is_sba():
            self.aut_b = aut_b
        else:
            self.aut_b = aut_b.postprocess('BA')

        self.state_encoding = {}

    def shuffle(self, disjunction=False):
        new_aut = spot.make_twa_graph()

        # We want to make sure that it visits infinitely often BOTH automata's accepting states
        if disjunction:
            new_aut.set_acceptance(2, 'Inf(0) | Inf(1)')
        else:
            new_aut.set_acceptance(2, 'Inf(0) & Inf(1)')

        new_aut.new_states(2 * self.aut_a.num_states() * self.aut_b.num_states())

        idx = 0
        for i in ['a', 'b']:
            for qa in range(self.aut_a.num_states()):
                for qb in range(self.aut_b.num_states()):
                    self.state_encoding[(i, qa, qb)] = idx
                    idx += 1

        for ap in self.aut_a.ap():
            buddy.bdd_ithvar(new_aut.register_ap(ap.ap_name()))
        for ap in self.aut_b.ap():
            buddy.bdd_ithvar(new_aut.register_ap(ap.ap_name()))

        a_init = self.aut_a.get_init_state_number()
        b_init = self.aut_b.get_init_state_number()
        new_aut.set_init_state(self.state_encoding[('a', a_init, b_init)])

        for e in self.aut_a.edges():
            for qb in range(self.aut_b.num_states()):
                src = self.state_encoding[('a', e.src, qb)]
                dst = self.state_encoding[('b', e.dst, qb)]
                acc = self.transform_acc(e.acc, 0)
                # print('Adding edge: {} -> {} with cond {} and acc {}'.format(src, dst, spot.bdd_to_formula(e.cond), acc))
                new_aut.new_edge(src, dst, e.cond, acc)

        for e in self.aut_b.edges():
            for qa in range(self.aut_a.num_states()):
                src = self.state_encoding[('b', qa, e.src)]
                dst = self.state_encoding[('a', qa, e.dst)]
                acc = self.transform_acc(e.acc, 1)
                # print('Adding edge: {} -> {} with cond {} and acc {}'.format(src, dst, spot.bdd_to_formula(e.cond), acc))
                new_aut.new_edge(src, dst, e.cond, acc)

        return new_aut.postprocess('BA')

    def transform_acc(self, acc, new_acc_num):
        if acc == spot.mark_t([0]):
            return spot.mark_t([new_acc_num])
        elif acc == spot.mark_t([]):
            return spot.mark_t([])
        else:
            raise Exception('Unexpected acceptance condition on edge: {}'.format(e.acc))

