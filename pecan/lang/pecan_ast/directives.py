#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import spot

from pecan.tools.convert_hoa import convert_hoa
from pecan.lang.pecan_ast.prog import *

class Directive(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __repr__(self):
        return '#{}'.format(self.name)

class DirectiveSaveAut(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def evaluate(self, prog):
        prog.call(self.pred_name).postprocess('BA').save(self.filename)
        return None

    def __repr__(self):
        return '#save_aut({}, {})'.format(str(self.filename), self.pred_name)

class DirectiveSaveAutImage(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
        self.filename = filename[1:-1]
        self.pred_name = pred_name

    def evaluate(self, prog):
        evaluated = prog.call(self.pred_name)
        with open(self.filename, 'w') as f:
            f.write(evaluated.show().data) # Write the raw svg data into the file

        return None

    def __repr__(self):
        return '#save_aut_img({}, {})'.format(repr(self.filename), self.pred_name)

class DirectiveSavePred(ASTNode):
    def __init__(self, filename, pred_name):
        super().__init__()
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

class DirectiveLoadPreds(ASTNode):
    def __init__(self, filename):
        super().__init__()
        self.filename = filename[1:-1]

    def evaluate(self, prog):
        realpath = prog.locate_file(self.filename)
        with open(realpath, 'r') as f:
            prog.parser.parse(f.read()).evaluate(prog)

        return None

    def __repr__(self):
        return '#load_preds({})'.format(repr(self.filename))

class DirectiveContext(ASTNode):
    def __init__(self, context_key, context_val):
        super().__init__()
        self.context_key = context_key
        self.context_val = context_val

    def evaluate(self, prog):
        prog.context[self.context_key] = self.context_val
        return None

    def __repr__(self):
        return '#context({})'.format(self.context)

class DirectiveEndContext(ASTNode):
    def __init__(self, context_key):
        super().__init__()
        self.context_key = context_key

    def evaluate(self, prog):
        prog.context.pop(self.context_key)
        return None

    def __repr__(self):
        return '#end_context({})'.format(self.context)

# Asserts that pred_name is truth_val: i.e., that pred_name is 'true' (always), 'false' (always), or 'sometimes' true
class DirectiveAssertProp(ASTNode):
    def __init__(self, truth_val, pred_name):
        super().__init__()
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

class DirectiveLoadAut(ASTNode):
    def __init__(self, filename, aut_format, pred_name, pred_args):
        super().__init__()
        self.filename = filename[1:-1]
        self.aut_format = aut_format[1:-1] # Remove the quotes at the beginning and end # TODO: Do this better
        self.pred_name = pred_name
        self.pred_args = pred_args

    def evaluate(self, prog):
        if self.aut_format == 'hoa':
            realpath = prog.locate_file(self.filename)
            aut = spot.automaton(realpath)
            prog.preds[self.pred_name] = NamedPred(self.pred_name, self.pred_args, AutLiteral(aut))
        elif self.aut_format == 'pecan':
            realpath = prog.locate_file(self.filename)
            convert_hoa(realpath, 'temp.aut')
            aut = spot.automaton('temp.aut')
            prog.preds[self.pred_name] = NamedPred(self.pred_name, self.pred_args, AutLiteral(aut))
        else:
            raise Exception('Unknown format: {}'.format(self.aut_format))

        return None

    def __repr__(self):
        return '#load({}, {}, {})'.format(self.filename, self.aut_format, self.pred_name)

