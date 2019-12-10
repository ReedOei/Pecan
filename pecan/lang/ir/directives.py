#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import sys

import spot

from pecan.tools.automaton_tools import TruthValue
from pecan.tools.convert_hoa import convert_aut
from pecan.lang.ir import *

class DirectiveSaveAut(IRNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename
        self.pred_name = pred_name

    def evaluate(self, prog):
        if not prog.quiet:
            print(f'[INFO] Saving {self.pred_name} as {self.filename}')

        prog.call(self.pred_name).postprocess('BA').save(self.filename)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAut(self)

    def __repr__(self):
        return '#save_aut({}, {})'.format(str(self.filename), self.pred_name)

class DirectiveSaveAutImage(IRNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename
        self.pred_name = pred_name

    def evaluate(self, prog):
        if not prog.quiet:
            # TODO: Support formats other than SVG?
            print(f'[INFO] Saving {self.pred_name} as an SVG in {self.filename}')

        evaluated = prog.call(self.pred_name).postprocess('BA')
        with open(self.filename, 'w') as f:
            f.write(evaluated.show().data) # Write the raw svg data into the file

        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAutImage(self)

    def __repr__(self):
        return '#save_aut_img({}, {})'.format(repr(self.filename), self.pred_name)

class DirectiveContext(IRNode):
    def __init__(self, context_key, context_val):
        super().__init__()
        self.context_key = context_key
        self.context_val = context_val

    def evaluate(self, prog):
        prog.context[self.context_key] = self.context_val
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveContext(self)

    def __repr__(self):
        return '#context({}, {})'.format(self.context_key, self.context_val)

class DirectiveEndContext(IRNode):
    def __init__(self, context_key):
        super().__init__()
        self.context_key = context_key

    def evaluate(self, prog):
        prog.context.pop(self.context_key)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveEndContext(self)

    def __repr__(self):
        return '#end_context({})'.format(self.context_key)

# Asserts that pred_name is truth_val: i.e., that pred_name is 'true' (always), 'false' (always), or 'sometimes' true
class DirectiveAssertProp(IRNode):
    def __init__(self, truth_val, pred_name):
        super().__init__()
        self.truth_val = truth_val
        self.pred_name = pred_name

    def pred_truth_value(self, prog):
        return TruthValue(Call(self.pred_name, [])).truth_value(prog)

    def evaluate(self, prog):
        if not prog.quiet:
            print(f'[INFO] Checking if {self.pred_name} is {self.display_truth_val()}.')

        pred_truth_value = self.pred_truth_value(prog)

        if pred_truth_value == self.truth_val:
            result = Result(f'{self.pred_name} is {self.display_truth_val()}.', True)
        else:
            result = Result(f'{self.pred_name} is not {self.display_truth_val()}.', False)

        if not prog.quiet:
            result.print_result()

        return result

    def transform(self, transformer):
        return transformer.transform_DirectiveAssertProp(self)

    def display_truth_val(self):
        if self.truth_val == 'sometimes':
            return 'sometimes true'
        else:
            return self.truth_val # 'true' or 'false'

    def __repr__(self):
        return '#assert_prop({}, {})'.format(self.truth_val, self.pred_name)

class DirectiveLoadAut(IRNode):
    def __init__(self, filename, aut_format, pred):
        super().__init__()
        self.filename = filename
        self.aut_format = aut_format
        self.pred = pred

    def evaluate(self, prog):
        if self.aut_format == 'hoa':
            realpath = prog.locate_file(self.filename)
            aut = spot.automaton(realpath)
            prog.preds[self.pred.name] = NamedPred(self.pred.name, self.pred.args, AutLiteral(aut))
        elif self.aut_format == 'pecan':
            realpath = prog.locate_file(self.filename)
            aut = convert_aut(realpath, self.pred.args)
            prog.preds[self.pred.name] = NamedPred(self.pred.name, self.pred.args, AutLiteral(aut))
        else:
            raise Exception('Unknown format: {}'.format(self.aut_format))

        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveLoadAut(self)

    def __repr__(self):
        return '#load({}, {}, {})'.format(self.filename, self.aut_format, repr(self.pred))

class DirectiveImport(IRNode):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def evaluate(self, prog):
        realpath = prog.locate_file(self.filename)
        new_prog = prog.loader(realpath).copy_defaults(prog)
        new_prog.evaluate()
        prog.include(new_prog)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveImport(self)

    def __repr__(self):
        return '#import({})'.format(repr(self.filename))

class DirectiveForget(IRNode):
    def __init__(self, var_name):
        super().__init__()
        self.var_name = var_name

    def evaluate(self, prog):
        prog.forget(self.var_name)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveForget(self)

    def __repr__(self):
        return '#forget({})'.format(repr(self.var_name))

class DirectiveType(IRNode):
    def __init__(self, pred_ref, val_dict):
        super().__init__()
        self.pred_ref = pred_ref
        self.val_dict = val_dict

    def evaluate(self, prog):
        prog.declare_type(self.pred_ref, self.val_dict)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveType(self)

    def __repr__(self):
        return '#type({}, {})'.format(self.pred_ref, self.val_dict)

class DirectiveShowWord(IRNode):
    def __init__(self, word_name, index_type, start_index, end_index):
        super().__init__()
        self.word_name = word_name

        from pecan.lang.type_inference import RestrictionType
        self.index_type = index_type if index_type is not None else None

        self.start_index = start_index
        self.end_index = end_index

    def evaluate(self, prog):
        from pecan.lang.ir.words import EqualsCompareIndex, Index
        from pecan.lang.ir.arith import IntConst
        from pecan.lang.typed_ir_lowering import TypedIRLowering

        lowerer = TypedIRLowering()

        # We are going to introduce new variables, via constants, and they'll need a scope to live in
        prog.enter_scope()

        # TODO: Eventually, optimize this. Or add procedures and just eliminate it altogether
        index_expr = lambda idx_val: lowerer.transform(EqualsCompareIndex(True, Index(self.word_name, IntConst(idx_val).with_type(self.index_type)), FormulaTrue()))

        for idx in range(self.start_index, self.end_index + 1):
            if TruthValue(index_expr(idx)).truth_value(prog) == 'true':
                sys.stdout.write('1')
                sys.stdout.flush()
            else:
                sys.stdout.write('0')
                sys.stdout.flush()

        sys.stdout.write('\n')

        prog.exit_scope()

        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveShowWord(self)

    def __repr__(self):
        return '#show_word({}, {}, {}, {})'.format(self.word_name, self.index_type, self.start_index, self.end_index)

