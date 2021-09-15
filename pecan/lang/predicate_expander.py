#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir import *

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.ir_substitution import IRSubstitution

class PredicateExpander(IRTransformer):
    def __init__(self, prog):
        super().__init__()
        self.prog = prog

    def transform_Call(self, node):
        if not node.args:
            final_call = node
        else:
            final_call = self.prog.lookup_dynamic_call(node.name, node.args)
        pred = self.prog.lookup_pred_by_name(final_call.name)
        subs = { arg: arg_val for arg, arg_val in zip(final_call.args, node.args) }
        return self.transform(IRSubstitution(subs).transform(pred.body))

