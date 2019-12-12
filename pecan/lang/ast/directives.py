#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import sys

import spot

from pecan.tools.automaton_tools import TruthValue
from pecan.tools.convert_hoa import convert_aut
from pecan.lang.ast import *

class Directive(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return '#{}'.format(self.name)

class DirectiveSaveAut(Directive):
    def __init__(self, filename, pred_name):
        super().__init__('save_aut')
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAut(self)

    def __repr__(self):
        return '#save_aut({}, {})'.format(str(self.filename), self.pred_name)

class DirectiveSaveAutImage(Directive):
    def __init__(self, filename, pred_name):
        super().__init__('save_aut_img')
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAutImage(self)

    def __repr__(self):
        return '#save_aut_img({}, {})'.format(repr(self.filename), self.pred_name)

class DirectiveContext(Directive):
    def __init__(self, context_key, context_val):
        super().__init__('context')
        self.context_key = context_key[1:-1]
        self.context_val = context_val[1:-1]

    def transform(self, transformer):
        return transformer.transform_DirectiveContext(self)

    def __repr__(self):
        return '#context({}, {})'.format(self.context_key, self.context_val)

class DirectiveEndContext(Directive):
    def __init__(self, context_key):
        super().__init__('end_context')
        self.context_key = context_key[1:-1]

    def transform(self, transformer):
        return transformer.transform_DirectiveEndContext(self)

    def __repr__(self):
        return '#end_context({})'.format(self.context_key)

# Asserts that pred_name is truth_val: i.e., that pred_name is 'true' (always), 'false' (always), or 'sometimes' true
class DirectiveAssertProp(Directive):
    def __init__(self, truth_val, pred_name):
        super().__init__('assert_prop')
        self.truth_val = truth_val
        self.pred_name = pred_name

    def transform(self, transformer):
        return transformer.transform_DirectiveAssertProp(self)

    def __repr__(self):
        return '#assert_prop({}, {})'.format(self.truth_val, self.pred_name)

class DirectiveLoadAut(Directive):
    def __init__(self, filename, aut_format, pred):
        super().__init__('load')
        self.filename = filename[1:-1]
        self.aut_format = aut_format[1:-1] # Remove the quotes at the beginning and end # TODO: Do this better
        self.pred = pred

    def transform(self, transformer):
        return transformer.transform_DirectiveLoadAut(self)

    def __repr__(self):
        return '#load({}, {}, {})'.format(self.filename, self.aut_format, repr(self.pred))

class DirectiveImport(Directive):
    def __init__(self, filename):
        super().__init__('import')
        self.filename = filename[1:-1]

    def transform(self, transformer):
        return transformer.transform_DirectiveImport(self)

    def __repr__(self):
        return '#import({})'.format(repr(self.filename))

class DirectiveForget(Directive):
    def __init__(self, var_name):
        super().__init__('forget')
        self.var_name = var_name

    def transform(self, transformer):
        return transformer.transform_DirectiveForget(self)

    def __repr__(self):
        return '#forget({})'.format(repr(self.var_name))

class DirectiveType(Directive):
    def __init__(self, pred_ref, val_dict):
        super().__init__('type')
        if type(pred_ref) is str:
            self.pred_ref = Call(pred_ref, [])
        else:
            self.pred_ref = pred_ref

        self.val_dict = val_dict

    def transform(self, transformer):
        return transformer.transform_DirectiveType(self)

    def __repr__(self):
        return '#type({}, {})'.format(self.pred_ref, self.val_dict)

class DirectiveShowWord(Directive):
    def __init__(self, word_name, index_type, start_index, end_index):
        super().__init__('show_word')
        self.word_name = word_name

        from pecan.lang.type_inference import RestrictionType
        self.index_type = RestrictionType(Call(index_type, [])) if index_type is not None else None

        self.start_index = start_index.evaluate_int(None)
        self.end_index = end_index.evaluate_int(None)

    def transform(self, transformer):
        return transformer.transform_DirectiveShowWord(self)

    def __repr__(self):
        return '#show_word({}, {}, {}, {})'.format(self.word_name, self.index_type, self.start_index, self.end_index)

