#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer

class BasicOptimizer(IRTransformer):
    def __init__(self):
        super().__init__()
        self.changed = False

    def optimize(self, node):
        self.changed = False

        new_node = self.transform(node)

        return self.changed, new_node

