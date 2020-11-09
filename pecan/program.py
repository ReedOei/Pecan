#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import os

from pecan.lang.parser import pecan_parser
from pecan.lang.type_inference import TypeInferer
from pecan.lang.ast_to_ir import ASTToIR
from pecan.lang.typed_ir_lowering import TypedIRLowering
from pecan.lang.optimizer.optimizer import UntypedOptimizer, Optimizer

from pecan.settings import settings

def make_search_paths(filename=None):
    own_path = os.path.dirname(os.path.realpath(__file__))
    std_library_path = os.path.join(own_path, '..', 'library')
    automata_library_path = os.path.join(own_path, '..', 'library', 'automata')

    # Always include the current directory and the standard library folder
    search_paths = ['.', std_library_path, automata_library_path]

    # If we're creating a search path for some file (which is almost always the case), then include the base directory of that file as well
    if filename is not None:
        search_paths.append(os.path.dirname(filename))

    search_paths.extend(settings.get_pecan_path())

    return search_paths

def load(pecan_file, *args, **kwargs):
    with open(pecan_file, 'r', encoding='utf-8') as f:
        kwargs['filename'] = pecan_file
        return from_source(f.read(), *args, **kwargs)

def from_source(source_code, *args, **kwargs):
    prog = pecan_parser.parse(source_code)

    settings.log(4, lambda: 'Parsed program:')
    settings.log(4, lambda: prog)

    prog.search_paths = make_search_paths(filename=kwargs.get('filename', None))
    prog.loader = load

    if settings.get_extract_implications():
        prog.extract_implications()

    prog = ASTToIR().transform(prog)

    settings.log(0, lambda: 'Search path: {}'.format(prog.search_paths))

    # Load the standard library
    prog = settings.include_stdlib(prog, load, args, kwargs)

    if settings.opt_enabled():
        prog = UntypedOptimizer(prog).optimize()

        settings.log(1, lambda: '(Untyped) Optimized program:')
        settings.log(1, lambda: prog)

    return prog

