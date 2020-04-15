#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

from pecan.lang.ir_transformer import IRTransformer
from pecan.lang.optimizer.basic_optimizer import BasicOptimizer

from pecan.lang.ir import *

class BooleanOptimizer(BasicOptimizer):
    def transform_Complement(self, node):
        if type(node.a) is Complement:
            # !(!P) is equivalent to P
            self.changed = True
            return self.transform(node.a.a)
        # DeMorgan's Laws: Pushing complements down seems to help
        elif type(node.a) is Conjunction:
            self.changed = True
            return self.transform(Disjunction(Complement(node.a.a), Complement(node.a.b)))
        elif type(node.a) is Disjunction:
            self.changed = True
            return self.transform(Conjunction(Complement(node.a.a), Complement(node.a.b)))

        # This transformation can let us avoid complements
        elif type(node.a) is Less:
            self.changed = True
            return self.transform(Disjunction(Less(node.a.b, node.a.a), Equals(node.a.a, node.a.b)))

        elif type(node.a) is BoolConst:
            self.changed = True
            return BoolConst(not node.a.bool_val)

        elif type(node.a) is Annotation:
            self.changed = True
            return Annotation(node.a.annotation_name, self.transform(Complement(node.a.body)))

        else:
            return super().transform_Complement(node)

    def transform_Conjunction(self, node):
        if type(node.a) is BoolConst:
            self.changed = True

            if node.a.bool_val:
                return self.transform(node.b)
            else:
                return BoolConst(False)

        elif type(node.b) is BoolConst:
            self.changed = True

            if node.b.bool_val:
                return self.transform(node.a)
            else:
                return BoolConst(False)

        else:
            return super().transform_Conjunction(node)

    def transform_Disjunction(self, node):
        if type(node.a) is BoolConst:
            self.changed = True

            if node.a.bool_val:
                return BoolConst(True)
            else:
                return self.transform(node.b)

        elif type(node.b) is BoolConst:
            self.changed = True

            if node.b.bool_val:
                return BoolConst(True)
            else:
                return self.transform(node.a)

        else:
            return super().transform_Disjunction(node)

    def transform_Equals(self, node: Equals):
        if node.a == node.b:
            self.changed = True
            return BoolConst(True)
        else:
            return super().transform_Equals(node)

