#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import argparse
import spot
import colorama

import os

from pecan.lang.parser import pecan_parser
import pecan.tools.theorem_generator as theorem_generator

PECAN_PATH_VAR = 'PECAN_PATH'

def run_repl(debug, env):
    while True:
        prog_str = input('> ')
        prog = pecan_parser.parse(prog_str)

        if debug:
            print(prog)

        env = prog.evaluate(env)

def make_search_paths():
    own_path = os.path.dirname(os.path.realpath(__file__))
    std_library_path = os.path.join(own_path, 'library')
    automata_library_path = os.path.join(own_path, 'library', 'automata')

    # Always include the current directory and the standard library folder
    search_paths = ['.', std_library_path, automata_library_path]

    if PECAN_PATH_VAR in os.environ:
        search_paths.extend(os.getenv(PECAN_PATH_VAR).split(os.pathsep))

    return search_paths

def main():
    parser = argparse.ArgumentParser(description='An automated theorem prover for Büchi Automata')
    parser.add_argument('file', help='A Pecan file to execute', nargs='?')
    parser.add_argument('-i', '--interactive', help='Run Pecan in interactive mode (REPL)', required=False, action='store_true')
    parser.add_argument('-d', '--debug', help='Output debugging information', required=False, action='store_true')
    parser.add_argument('-q', '--quiet', help='Quiet mode', required=False, action='store_true')
    parser.add_argument('--generate', help='Enumerate true statements, argument is how many variables to use', type=int, required=False)

    args = parser.parse_args()

    if args.generate is not None:
        for pred in theorem_generator.gen_thms(args.generate):
            print(pred)
    elif args.file is not None:
        with open(args.file, 'r') as f:
            prog = pecan_parser.parse(f.read())

        prog.parser = pecan_parser
        prog.debug = args.debug
        prog.quiet = args.quiet
        prog.search_paths = make_search_paths()

        env = prog.evaluate()

        if args.interactive:
            run_repl(args.debug, env)
    else:
        parser.print_help()

if __name__ == '__main__':
    colorama.init()
    spot.setup()
    main()

