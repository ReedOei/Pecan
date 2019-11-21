#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import argparse
import spot
import colorama

import os

from pecan.lang.parser import pecan_parser
from pecan.lang.pecan_ast import Program
import pecan.tools.theorem_generator as theorem_generator
from pecan import program

def run_repl(debug, env):
    while True:
        prog_str = input('> ')
        prog = pecan_parser.parse(prog_str)

        if debug:
            print(prog)

        env = prog.evaluate(env)

def main():
    parser = argparse.ArgumentParser(description='An automated theorem prover for Büchi Automata')
    parser.add_argument('file', help='A Pecan file to execute', nargs='?')
    parser.add_argument('-i', '--interactive', help='Run Pecan in interactive mode (REPL)', required=False, action='store_true')
    parser.add_argument('-d', '--debug', help='Output debugging information', required=False, action='store_true')
    parser.add_argument('-q', '--quiet', help='Quiet mode', required=False, action='store_true')
    parser.add_argument('--load_stdlib', help='Loads the standard library (from library/std.pn in your Pecan installation)', required=False, action='store_false')
    parser.add_argument('--generate', help='Enumerate true statements, argument is how many variables to use', type=int, required=False)

    args = parser.parse_args()

    env = None
    if args.generate is not None:
        for pred in theorem_generator.gen_thms(args.generate):
            print(pred)
    elif args.file is not None:
        prog = program.load(args.file, quiet=args.quiet, debug=args.debug, load_stdlib=args.load_stdlib)
        if args.debug:
            print('Parsed program:')
            print(prog)
        env = prog.evaluate()
    elif not args.interactive:
        parser.print_help()

    if args.interactive:
        if env is None:
            prog = Program([])

            prog.parser = pecan_parser
            prog.debug = args.debug
            prog.quiet = args.quiet
            prog.search_paths = make_search_paths()

            env = prog.evaluate()

        run_repl(args.debug, env)

if __name__ == '__main__':
    colorama.init()
    spot.setup()
    main()

