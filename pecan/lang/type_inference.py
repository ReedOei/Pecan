#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast_transformer import AstTransformer

class TypeInferer(AstTransformer):
    def __init__(self):
        super().__init__()

