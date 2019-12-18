#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import sys

import spot

from pecan.tools.automaton_tools import TruthValue
from pecan.tools.shuffle_automata import ShuffleAutomata
from pecan.tools.convert_hoa import convert_aut
from pecan.tools.labeled_aut_converter import convert_labeled_aut
from pecan.lang.ir import *

from pecan.settings import settings

class DirectiveSaveAut(IRNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename
        self.pred_name = pred_name

    def evaluate(self, prog):
        settings.log(f'[INFO] Saving {self.pred_name} as {self.filename}')

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
        settings.log(f'[INFO] Saving {self.pred_name} as an SVG in {self.filename}')

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
        return TruthValue(Call(self.pred_name, [])).truth_value(prog)

    def evaluate(self, prog):
        settings.log(f'[INFO] Checking if {self.pred_name} is {self.display_truth_val()}.')

        pred_truth_value = self.pred_truth_value(prog)

        if pred_truth_value == self.truth_val:
            result = Result(f'{self.pred_name} is {self.display_truth_val()}.', True)
        else:
            result = Result(f'{self.pred_name} is not {self.display_truth_val()}.', False)

        settings.log(result.result_str())

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
        self.pred = pred.with_parent(self)

    def evaluate(self, prog):
        # TODO: Support argument restrictions on loaded automata
        realpath = prog.locate_file(self.filename)

        if self.aut_format == 'hoa':
            # TODO: Rename the APs of the loaded automaton to be the same as the args specified
            aut = spot.automaton(realpath)
        elif self.aut_format == 'walnut':
            aut = convert_aut(realpath, [v.var_name for v in self.pred.args])
        elif self.aut_format == 'pecan':
            aut = convert_labeled_aut(realpath, [v.var_name for v in self.pred.args])
        else:
            raise Exception('Unknown format: {}'.format(self.aut_format))

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
        self.val_dict = {k: v.with_parent(self) for k, v in val_dict.items()}

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

class DirectiveShowWord(IRNode):
    def __init__(self, word_name, index_type, start_index, end_index):
        super().__init__()
        self.word_name = word_name

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

    def __eq__(self, other):
        return other is not None and type(other) is self.__class__ and \
               self.word_name == other.word_name and self.index_type == other.index_type and self.start_index == other.start_index and self.end_index == other.end_index

    def __hash__(self):
        return hash((self.word_name, self.index_type, self.start_index, self.end_index))

class DirectiveAcceptingWord(IRNode):
    def __init__(self, pred_name):
        super().__init__()
        self.pred_name = pred_name

    def transform(self, transformer):
        return transformer.transform_DirectiveAcceptingWord(self)

    # TODO: Remove this, an add a more extensible method for doing this sort of thing
    def to_binary(self, var_names, bdd_list):
        var_vals = {k: '' for k in var_names}

        for bdd in bdd_list:
            formula = spot.bdd_to_formula(bdd)

            next_vals = {}
            self.process_formula(next_vals, formula)

            # If we didn't find a value for a variable in this part of the formula, that means it can be either 0 or 1.
            # We arbitrarily choose 0.
            for var_name in var_names:
                var_vals[var_name] += next_vals.get(var_name, '0')

        return var_vals

    def process_formula(self, next_vals, formula):
        if formula._is(spot.op_ap):
            next_vals[formula.ap_name()] = "1"
        elif formula._is(spot.op_Not):
            next_vals[formula[0].ap_name()] = "0"
        elif formula._is(spot.op_And):
            for i in range(formula.size()):
                self.process_formula(next_vals, formula[i])
        elif formula._is(spot.op_tt):
            pass
        else:
            raise Exception('Cannot process formula: {}'.format(formula))

    def format_real(self, prefix, cycle):
        # It is possible for the whole number to be in the cycle (e.g., if the integral part is 0^w)
        if len(prefix) == 0:
            cycle_offset = 1
            sign = '+' if cycle[0] == '0' else '-'
        else:
            cycle_offset = 0
            sign = '+' if prefix[0] == '0' else '-'

        integral = ''
        # This is always just zeros, so don't bother showing it
        integral_repeat = ''
        fractional = ''
        fractional_repeat = ''

        # Need to keep track of which part will have
        fractional_modulus = 0
        for i, c in enumerate(prefix[1:]):
            if i % 2 == 0:
                fractional_modulus = 1
                fractional += c
            else:
                fractional_modulus = 0
                integral += c

        fractional_modulus = (fractional_modulus + cycle_offset) % 2
        for i, c in enumerate(cycle):
            if i % 2 == fractional_modulus:
                fractional_repeat += c
            else:
                integral_repeat += c

        # We store the integral part in LSD first
        integral = integral[::-1]
        integral_repeat = integral_repeat[::-1]

        if len(integral) > 0:
            return '{}{}.{}({})^w'.format(sign, integral, fractional, fractional_repeat)
        else:
            return '{}({})^w.{}({})^w'.format(sign, integral_repeat, fractional, fractional_repeat)

    def evaluate(self, prog):
        acc_word = prog.call(self.pred_name).accepting_word()

        if acc_word is not None:
            acc_word.simplify()

        print(acc_word)

        if acc_word is not None:
            var_vals = {}
            var_names = []
            for formula in list(acc_word.prefix) + list(acc_word.cycle):
                for f in spot.atomic_prop_collect(spot.bdd_to_formula(formula)):
                    var_names.append(f.ap_name())
            var_names = list(set(var_names))
            prefixes = self.to_binary(var_names, acc_word.prefix)
            cycles = self.to_binary(var_names, acc_word.cycle)

            for var_name in var_names:
                print('{}: {}({})^w'.format(var_name, prefixes[var_name], cycles[var_name]))

            # for var_name in var_names:
            #     # TODO: Allow users to define their own formatters here
            #     print('{}: {}'.format(var_name, self.format_real(prefixes[var_name], cycles[var_name])))

            acc_word.as_automaton().postprocess('BA').save('{}.aut'.format(self.pred_name))

        return None

    def __repr__(self):
        return '#accepting_word({})'.format(self.pred_name)

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
        aut_res = ShuffleAutomata(a_aut, b_aut).shuffle(self.disjunction)
        prog.preds[self.output_pred.name] = NamedPred(self.output_pred.name, self.output_pred.args, {}, AutLiteral(aut_res))

        return None

    def __repr__(self):
        return '#shuffle({}, {}, {})'.format(self.pred_a, self.pred_b, self.output_pred)

