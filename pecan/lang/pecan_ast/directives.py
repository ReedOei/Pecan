#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.tools.convert_hoa import convert_hoa
from pecan.lang.pecan_ast import *

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

    def evaluate(self, prog):
        prog.call(self.pred_name).postprocess('BA').save(self.filename)
        return None

    def __repr__(self):
        return '#save_aut({}, {})'.format(str(self.filename), self.pred_name)

class DirectiveSaveAutImage(Directive):
    def __init__(self, filename, pred_name):
        super().__init__('save_aut_img')
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def evaluate(self, prog):
        evaluated = prog.call(self.pred_name)
        with open(self.filename, 'w') as f:
            f.write(evaluated.show().data) # Write the raw svg data into the file

        return None

    def __repr__(self):
        return '#save_aut_img({}, {})'.format(repr(self.filename), self.pred_name)

class DirectiveSavePred(Directive):
    def __init__(self, filename, pred_name):
        super().__init__('save_pred')
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def evaluate(self, prog):
        try:
            with open(self.filename, 'r') as f:
                new_prog = prog.parser.parse(f.read())

            with open(self.filename, 'w') as f:
                for d in new_prog.defs:
                    if type(d) is NamedPred and d.name == self.pred_name:
                        self.write_pred(f, prog)
                    else:
                        f.write(repr(d))
                        f.write('\n')
        except FileNotFoundError: # No problem, just create the file
            with open(self.filename, 'w') as f:
                self.write_pred(f, prog)

    def write_pred(self, f, prog):
        for k, v in prog.context.items():
            f.write(repr(DirectiveContext(k, v)))
            f.write('\n')
        f.write(repr(prog.preds[self.pred_name])) # Write the predicate definition itself into the file
        f.write('\n')
        for ctx in prog.context[::-1]:
            f.write(repr(DirectiveEndContext(k)))
            f.write('\n')

    def __repr__(self):
        return '#save_pred({}, {})'.format(repr(self.filename), self.pred_name)

class DirectiveContext(Directive):
    def __init__(self, context_key, context_val):
        super().__init__('context')
        self.context_key = context_key[1:-1]
        self.context_val = context_val[1:-1]

    def evaluate(self, prog):
        prog.context[self.context_key] = self.context_val
        return None

    def __repr__(self):
        return '#context({}, {})'.format(self.context_key, self.context_val)

class DirectiveEndContext(Directive):
    def __init__(self, context_key):
        super().__init__('end_context')
        self.context_key = context_key[1:-1]

    def evaluate(self, prog):
        prog.context.pop(self.context_key)
        return None

    def __repr__(self):
        return '#end_context({})'.format(self.context)

# Asserts that pred_name is truth_val: i.e., that pred_name is 'true' (always), 'false' (always), or 'sometimes' true
class DirectiveAssertProp(Directive):
    def __init__(self, truth_val, pred_name):
        super().__init__('assert_prop')
        self.truth_val = truth_val
        self.pred_name = pred_name

    def pred_truth_value(self, prog):
        evaluated = prog.call(self.pred_name)
        if evaluated.is_empty(): # If we accept nothing, we are false
            return 'false'
        elif spot.complement(evaluated).is_empty(): # If our complement accepts nothing, we accept everything, so we are true
            return 'true'
        else: # Otherwise, we are neither true nor false: i.e., not all variables have been eliminated
            return 'sometimes'

    def evaluate(self, prog):
        pred_truth_value = self.pred_truth_value(prog)

        if pred_truth_value == self.truth_val:
            result = Result(f'{self.pred_name} is {self.display_truth_val()}.', True)
        else:
            result = Result(f'{self.pred_name} is not {self.display_truth_val()}.', False)

        if not prog.quiet:
            result.print_result()

        return result

    def display_truth_val(self):
        if self.truth_val == 'sometimes':
            return 'sometimes true'
        else:
            return self.truth_val # 'true' or 'false'

    def __repr__(self):
        return '#assert_prop({}, {})'.format(self.truth_val, self.pred_name)

class DirectiveLoadAut(Directive):
    def __init__(self, filename, aut_format, pred):
        super().__init__('load')
        self.filename = filename[1:-1]
        self.aut_format = aut_format[1:-1] # Remove the quotes at the beginning and end # TODO: Do this better
        self.pred = pred

    def evaluate(self, prog):
        if self.aut_format == 'hoa':
            realpath = prog.locate_file(self.filename)
            aut = spot.automaton(realpath)
            prog.preds[self.pred.name] = NamedPred(self.pred.name, self.pred.args, AutLiteral(aut))
        elif self.aut_format == 'pecan':
            realpath = prog.locate_file(self.filename)
            convert_hoa(realpath, 'temp.aut')
            aut = spot.automaton('temp.aut')
            prog.preds[self.pred.name] = NamedPred(self.pred.name, self.pred.args, AutLiteral(aut))
        else:
            raise Exception('Unknown format: {}'.format(self.aut_format))

        return None

    def __repr__(self):
        return '#load({}, {}, {})'.format(self.filename, self.aut_format, repr(self.pred))

class DirectiveImport(Directive):
    def __init__(self, filename):
        super().__init__('import')
        self.filename = filename[1:-1]

    def evaluate(self, prog):
        realpath = prog.locate_file(self.filename)
        new_prog = prog.loader(realpath, debug=prog.debug, quiet=prog.quiet)
        new_prog.evaluate()
        prog.include(new_prog)
        return None

    def __repr__(self):
        return '#import({})'.format(repr(self.filename))

class DirectiveForget(Directive):
    def __init__(self, var_name):
        super().__init__('forget')
        self.var_name = var_name

    def evaluate(self, prog):
        prog.forget(self.var_name)
        return None

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

    def evaluate(self, prog):
        prog.declare_type(self.pred_ref, self.val_dict)
        return None

    def __repr__(self):
        return '#type({}, {})'.format(self.pred_ref, self.val_dict)

