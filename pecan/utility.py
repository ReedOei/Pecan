#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import copy
import os

# From: https://stackoverflow.com/a/6222692/1498618
def touch(fname):
    try:
        os.utime(fname, None)
    except OSError:
        with open(fname, 'a'):
            pass

class VarMap:
    def __init__(self, var_reps=None):
        self.var_reps = var_reps or {}

    def clone(self):
        return VarMap(copy.deepcopy(self.var_reps))

    def __contains__(self, item):
        return item in self.var_reps

    def __getitem__(self, item):
        return self.var_reps[item]

    def __setitem__(self, item, value):
        self.var_reps[item] = value

    def items(self):
        return self.var_reps.items()

    def pop(self, k):
        return self.var_reps.pop(k)

    def merge_with(self, other_map):
        merged_var_map = self.clone()

        # The substitutions that need to be made to the representation values for this merge to be valid
        subs = {}

        for var, reps in other_map.var_reps.items():
            if var in merged_var_map:
                merged_reps = merged_var_map[var]

                if len(merged_reps) != len(reps):
                    raise Exception('Cannot merge {}: representations differ in length ({}, {})'.format(var, merged_reps, reps))

                for a, b in zip(merged_reps, reps):
                    subs[b] = a
            else:
                merged_var_map[var] = reps

        return merged_var_map, subs

    def get_or_gen(self, var_name, gen_func, n_reps):
        if var_name not in self:
            self[var_name] = [ gen_func() for _ in range(n_reps) ]

        return self[var_name]

    def __repr__(self):
        return 'VarMap({})'.format(self.var_reps)

    def update(self, other):
        self.var_reps.update(other.var_reps)

    def to_str(self):
        return repr(self.var_reps)

