#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast import *

from pecan.lang.ast_transformer import AstTransformer

class ASTSubstitution(AstTransformer):
    def __init__(self, subs):
        super().__init__()
        self.subs = subs

    def transform_str(self, original_str):
        return self.subs.get(original_str, original_str)

    def transform_VarRef(self, node):
        return self.subs.get(node.var_name, node)

