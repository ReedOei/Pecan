#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.lang.ast import *

class DirectiveSaveAut(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename
        self.pred_name = pred_name

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAut(self)

    def __repr__(self):
        return '#save_aut({}, {})'.format(str(self.filename), self.pred_name)

class DirectiveSaveAutImage(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename
        self.pred_name = pred_name

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAutImage(self)

    def __repr__(self):
        return '#save_aut_img({}, {})'.format(repr(self.filename), self.pred_name)

class DirectiveContext(ASTNode):
    def __init__(self, context_key, context_val):
        super().__init__()
        self.context_key = context_key
        self.context_val = context_val

    def transform(self, transformer):
        return transformer.transform_DirectiveContext(self)

    def __repr__(self):
        return '#context({}, {})'.format(self.context_key, self.context_val)

class DirectiveEndContext(ASTNode):
    def __init__(self, context_key):
        super().__init__()
        self.context_key = context_key

    def transform(self, transformer):
        return transformer.transform_DirectiveEndContext(self)

    def __repr__(self):
        return '#end_context({})'.format(self.context_key)

# Asserts that pred_name is truth_val: i.e., that pred_name is 'true' (always), 'false' (always), or 'sometimes' true
class DirectiveAssertProp(ASTNode):
    def __init__(self, truth_val, pred_name):
        super().__init__()
        self.truth_val = truth_val
        self.pred_name = pred_name

    def transform(self, transformer):
        return transformer.transform_DirectiveAssertProp(self)

    def __repr__(self):
        return '#assert_prop({}, {})'.format(self.truth_val, self.pred_name)

class DirectiveLoadAut(ASTNode):
    def __init__(self, filename, aut_format, pred):
        super().__init__()
        self.filename = filename
        self.aut_format = aut_format
        self.pred = pred

    def transform(self, transformer):
        return transformer.transform_DirectiveLoadAut(self)

    def __repr__(self):
        return '#load("{}", "{}", {})'.format(self.filename, self.aut_format, repr(self.pred))

class DirectiveImport(ASTNode):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def transform(self, transformer):
        return transformer.transform_DirectiveImport(self)

    def __repr__(self):
        return '#import({})'.format(repr(self.filename))

class DirectiveForget(ASTNode):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def transform(self, transformer):
        return transformer.transform_DirectiveForget(self)

    def __repr__(self):
        return '#forget({})'.format(repr(self.var_name))

class DirectiveStructure(ASTNode):
    def __init__(self, pred_ref, val_dict):
        super().__init__()

        if type(pred_ref) is VarRef:
            self.pred_ref = Call(pred_ref.var_name, [VarRef('*')])
        elif type(pred_ref) is Call:
            self.pred_ref = pred_ref.add_arg(VarRef('*'))
        else:
            raise Exception('Pred ref {} is not a VarRef or Call'.format(pred_ref))

        self.val_dict = val_dict

    def transform(self, transformer):
        return transformer.transform_DirectiveStructure(self)

    def __repr__(self):
        return 'Structure {} defining {} .'.format(self.pred_ref, self.val_dict)

class DirectiveShuffle(ASTNode):
    def __init__(self, disjunction, pred_a, pred_b, output_pred):
        super().__init__()
        self.disjunction = disjunction
        self.pred_a = pred_a
        self.pred_b = pred_b
        self.output_pred = output_pred

    def transform(self, transformer):
        return transformer.transform_DirectiveShuffle(self)

    def __repr__(self):
        return '#shuffle({}, {}, {})'.format(self.pred_a, self.pred_b, self.output_pred)

