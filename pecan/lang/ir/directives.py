#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import sys

from pecan.tools.shuffle_automata import ShuffleAutomata
from pecan.tools.convert_hoa import convert_aut
from pecan.tools.labeled_aut_converter import convert_labeled_aut
from pecan.tools.hoa_loader import load_hoa
from pecan.automata.buchi import BuchiAutomaton
from pecan.lang.ir import *

from pecan.settings import settings

class DirectiveSaveAut(IRNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename
        self.pred_name = pred_name

    def evaluate(self, prog):
        settings.log(lambda: f'[INFO] Saving {self.pred_name} as {self.filename}')

        prog.call(self.pred_name).save(self.filename)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAut(self)

    def __repr__(self):
        return '#save_aut({}, {})'.format(str(self.filename), self.pred_name)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.filename == other.filename and self.pred_name == other.pred_name

    def __hash__(self):
        return hash((self.filename, self.pred_name))

class DirectiveSaveAutImage(IRNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename
        self.pred_name = pred_name

    def evaluate(self, prog):
        # TODO: Support formats other than SVG?
        settings.log(lambda: f'[INFO] Saving {self.pred_name} as an SVG in {self.filename}')

        evaluated = prog.call(self.pred_name)
        with open(self.filename, 'w') as f:
            f.write(evaluated.show().data) # Write the raw svg data into the file

        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveSaveAutImage(self)

    def __repr__(self):
        return '#save_aut_img({}, {})'.format(repr(self.filename), self.pred_name)

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.filename == other.filename and self.pred_name == other.pred_name

    def __hash__(self):
        return hash((self.filename, self.pred_name))

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

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.context_key == other.context_key and self.context_val == other.context_val

    def __hash__(self):
        return hash((self.context_key, self.context_val))

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

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.context_key == other.context_key

    def __hash__(self):
        return hash(self.context_key)

# Asserts that pred_name is truth_val: i.e., that pred_name is 'true' (always), 'false' (always), or 'sometimes' true
class DirectiveAssertProp(IRNode):
    def __init__(self, truth_val, pred_name):
        super().__init__()
        self.truth_val = truth_val
        self.pred_name = pred_name

    def pred_truth_value(self, prog):
        return Call(self.pred_name, []).evaluate(prog).truth_value()

    def evaluate(self, prog):
        settings.log(lambda: f'[INFO] Checking if {self.pred_name} is {self.display_truth_val()}.')

        pred_truth_value = self.pred_truth_value(prog)

        if pred_truth_value == self.truth_val:
            result = Result(f'{self.pred_name} is {self.display_truth_val()}.', True)
        else:
            result = Result(f'{self.pred_name} is not {self.display_truth_val()}.', False)

        settings.log(lambda: result.result_str())

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

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and self.truth_val == other.truth_val and self.pred_name == other.pred_name

    def __hash__(self):
        return hash((self.truth_val, self.pred_name))

class DirectiveLoadAut(IRNode):
    def __init__(self, filename, aut_format, pred):
        super().__init__()
        self.filename = filename
        self.aut_format = aut_format
        self.pred = pred

    def evaluate(self, prog):
        # TODO: Support argument restrictions on loaded automata
        realpath = prog.locate_file(self.filename)

        if self.aut_format == 'hoa':
            # TODO: Rename the APs of the loaded automaton to be the same as the args specified
            aut = load_hoa(realpath)
        elif self.aut_format == 'walnut':
            aut = convert_aut(realpath, [v.var_name for v in self.pred.args])
        elif self.aut_format == 'pecan':
            aut = convert_labeled_aut(realpath, [v.var_name for v in self.pred.args])
        else:
            raise Exception('Unknown format: {}'.format(self.aut_format))

        # print('loaded ap: ', aut.aut.ap())

        prog.preds[self.pred.name] = NamedPred(self.pred.name, self.pred.args, {}, AutLiteral(aut))

        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveLoadAut(self)

    def __repr__(self):
        return '#load({}, {}, {})'.format(self.filename, self.aut_format, repr(self.pred))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and \
               self.filename == other.filename and self.aut_format == other.aut_format and self.pred == other.pred

    def __hash__(self):
        return hash((self.filename, self.aut_format, self.pred))

class DirectiveImport(IRNode):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def evaluate(self, prog):
        realpath = prog.locate_file(self.filename)
        from pecan.program import load
        new_prog = load(realpath).copy_defaults(prog)
        new_prog.evaluate()
        prog.include(new_prog)
        return None

    def transform(self, transformer):
        return transformer.transform_DirectiveImport(self)

    def __repr__(self):
        return '#import({})'.format(repr(self.filename))

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and \
               self.filename == other.filename

    def __hash__(self):
        return hash(self.filename)

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

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and \
               self.var_name == other.var_name

    def __hash__(self):
        return hash(self.var_name)

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

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and \
               self.pred_ref == other.pred_ref and self.val_dict == other.val_dict

    def __hash__(self):
        return hash((self.pred_ref, self.val_dict))

class DirectiveShuffle(IRNode):
    def __init__(self, disjunction, pred_a, pred_b, output_pred):
        super().__init__()
        self.disjunction = disjunction
        self.pred_a = pred_a
        self.pred_b = pred_b
        self.output_pred = output_pred

    def transform(self, transformer):
        return transformer.transform_DirectiveShuffle(self)

    def evaluate(self, prog):
        a_aut = prog.call(self.pred_a.name, self.pred_a.args)
        b_aut = prog.call(self.pred_b.name, self.pred_b.args)
        aut_res = BuchiAutomaton(ShuffleAutomata(BuchiAutomaton.as_buchi(a_aut).get_aut(), BuchiAutomaton.as_buchi(b_aut).get_aut()).shuffle(self.disjunction))
        prog.preds[self.output_pred.name] = NamedPred(self.output_pred.name, self.output_pred.args, {}, AutLiteral(aut_res))

        return None

    def __repr__(self):
        return '#shuffle({}, {}, {})'.format(self.pred_a, self.pred_b, self.output_pred)

