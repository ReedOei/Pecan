#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir import *

from pecan.settings import settings

class Annotation(IRPredicate):
    def __init__(self, annotation_name, body):
        super().__init__()
        self.annotation_name = annotation_name
        self.body = body

    def evaluate_node(self, prog):
        if self.annotation_name == '@no_simplify':
            orig_level = settings.get_simplication_level()
            settings.set_simplification_level(0)
            res = self.body.evaluate(prog)
            settings.set_simplification_level(orig_level)
            return res
        elif self.annotation_name == '@simplify':
            orig_level = settings.get_simplication_level()
            settings.set_simplification_level(1)
            res = self.body.evaluate(prog)
            settings.set_simplification_level(orig_level)
            return res
        elif self.annotation_name == '@postprocess':
            return self.body.evaluate(prog).postprocess()
        elif self.annotation_name == '@simplify_states':
            return self.body.evaluate(prog).simplify_states()
        elif self.annotation_name == '@simplify_edges':
            return self.body.evaluate(prog).simplify_edges()
        elif self.annotation_name == '@merge_states':
            return self.body.evaluate(prog).merge_states()
        elif self.annotation_name == '@merge_edges':
            return self.body.evaluate(prog).merge_edges()
        # elif self.annotation_name == '@minimize':
        #     return self.body.evaluate(prog).minimize()
        else:
            raise Exception('Unknown annotation: {}'.format(self.annotation_name))

    def transform(self, transformer):
        return transformer.transform_Annotation(self)

    def __repr__(self):
        return '{}[{}]'.format(self.annotation_name, self.body)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.annotation_name == other.annotation_name and self.body == other.body

    def __hash__(self):
        return hash((self.annotation_name, self.body))

