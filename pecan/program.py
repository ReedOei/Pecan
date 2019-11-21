#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import os

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import Program

PECAN_PATH_VAR = 'PECAN_PATH'

def make_search_paths(filename=None):
    own_path = os.path.dirname(os.path.realpath(__file__))
    std_library_path = os.path.join(own_path, '..', 'library')
    automata_library_path = os.path.join(own_path, '..', 'library', 'automata')

    # Always include the current directory and the standard library folder
    search_paths = ['.', std_library_path, automata_library_path]

    # If we're creating a search path for some file (which is almost always the case), then include the base directory of that file as well
    if filename is not None:
        search_paths.append(os.path.dirname(filename))

    if PECAN_PATH_VAR in os.environ:
        search_paths.extend(os.getenv(PECAN_PATH_VAR).split(os.pathsep))

    return search_paths

def load(pecan_file, *args, **kwargs):
    with open(pecan_file, 'r') as f:
        kwargs['filename'] = pecan_file
        return from_source(f.read(), *args, **kwargs)

def from_source(source_code, *args, **kwargs):
    prog = pecan_parser.parse(source_code)

    prog.debug = kwargs.get('debug', False)
    prog.quiet = kwargs.get('quiet', False)
    prog.search_paths = make_search_paths(kwargs.get('filename', None))
    prog.loader = load

    # Load the standard library
    if kwargs.get('load_stdlib', True):
        kwargs_copy = dict(kwargs)
        # Don't load stdlib again (prevent infinite loop)
        kwargs_copy['load_stdlib'] = False
        kwargs_copy['quiet'] = kwargs.get('quiet_stdlib', kwargs.get('quiet', False))

        stdlib_prog = load(prog.locate_file('std.pn'), *args, **kwargs_copy)
        stdlib_prog.evaluate()
        prog.include(stdlib_prog)

    if prog.debug:
        print('Search path: {}'.format(prog.search_paths))

    return prog

