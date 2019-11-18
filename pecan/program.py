#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import os

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import Program

PECAN_PATH_VAR = 'PECAN_PATH'

def make_search_paths():
    own_path = os.path.dirname(os.path.realpath(__file__))
    std_library_path = os.path.join(own_path, '..', 'library')
    automata_library_path = os.path.join(own_path, '..', 'library', 'automata')

    # Always include the current directory and the standard library folder
    search_paths = ['.', std_library_path, automata_library_path]

    if PECAN_PATH_VAR in os.environ:
        search_paths.extend(os.getenv(PECAN_PATH_VAR).split(os.pathsep))

    return search_paths

def load(filename, *args, **kwargs):
    with open(filename, 'r') as f:
        prog = pecan_parser.parse(f.read())

    prog.parser = pecan_parser
    prog.debug = kwargs.get('debug', False)
    prog.quiet = kwargs.get('quiet', False)
    prog.search_paths = make_search_paths()

    if prog.debug:
        print('Path: {}'.format(prog.search_paths))

    return prog

