#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ast import *

class Annotation(Predicate):
    def __init__(self, annotation_name, body):
        super().__init__()
        self.annotation_name = annotation_name
        self.body = body

    def transform(self, transformer):
        return transformer.transform_Annotation(self)

    def __repr__(self):
        return '{}[{}]'.format(self.annotation_name, self.body)

