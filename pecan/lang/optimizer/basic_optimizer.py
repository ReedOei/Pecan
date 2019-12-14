#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer

class BasicOptimizer(IRTransformer):
    def __init__(self, master_optimizer):
        super().__init__()
        self.changed = False
        self.master_optimizer = master_optimizer
        self.prog = master_optimizer.prog
        self.pred = None

    def pre_optimize(self, node):
        pass

    def post_optimize(self, node):
        pass

    def optimize(self, node, pred):
        self.changed = False

        self.pred = pred

        self.pre_optimize(node)
        new_node = self.transform(node)
        self.post_optimize(new_node)

        return self.changed, new_node

