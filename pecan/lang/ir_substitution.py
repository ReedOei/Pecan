#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir import *

from pecan.lang.ir_transformer import IRTransformer

class IRSubstitution(IRTransformer):
    def __init__(self, subs):
        super().__init__()
        self.subs = subs

    def transform_str(self, original_str):
        return self.substitute_identifier(None, original_str)

    def substitute_identifier(self, node, original_str):
        if original_str in self.subs:
            if type(self.subs[original_str]) is PralineString:
                return self.subs[original_str].get_value()
            else:
                raise Exception('Cannot substitute a non-string for an identifier in "{}"; subs: {}'.format(node, self.subs))
        else:
            return original_str

    def transform_VarRef(self, node):
        if node.var_name in self.subs:
            return self.subs[node.var_name]
        else:
            return node

    def transform_Call(self, node):
        new_args = [self.transform(arg) for arg in node.args]
        if node.name in self.subs:
            sub = self.subs[node.name]
            if isinstance(sub, PralineString):
                return Call(sub.get_value(), new_args).with_type(node.get_type())
            elif isinstance(sub, PralinePecanLiteral) and isinstance(sub.get_term(), Call):
                call = sub.get_term()
                return Call(call.name, call.args + new_args).with_type(node.get_type())
            else:
                raise Exception('Cannot substitute a non-string or non-call for an identifier in "{}"; subs: {}'.format(node, self.subs))
        else:
            return Call(node.name, new_args).with_type(node.get_type())

    def transform_NamedPred(self, node):
        new_name = self.substitute_identifier(node, node.name)
        new_args = [self.transform(arg) for arg in node.args]
        new_restrictions = {self.transform(var): self.transform(restriction) for var, restriction in node.arg_restrictions.items()}
        return NamedPred(new_name, new_args, new_restrictions, self.transform(node.body), restriction_env=node.restriction_env, body_evaluated=node.body_evaluated, arg_name_map=node.arg_name_map)

