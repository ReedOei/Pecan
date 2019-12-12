#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import argparse
import spot

import colorama
import readline

import os

import pecan.tools.theorem_generator as theorem_generator
from pecan import program

def run_repl(env):
    while True:
        try:
            prog_str = input('> ')

            if prog_str.strip().lower() == 'exit':
                break

            prog = program.from_source(prog_str)

            if env.debug > 0:
                print(prog)

            env = prog.evaluate(env)
        except KeyboardInterrupt:
            print('') # newline to go "below" the prompt
            print("Use 'exit' to exit Pecan.")
        except EOFError:
            break

def main():
    parser = argparse.ArgumentParser(description='An automated theorem prover for Büchi Automata')
    parser.add_argument('file', help='A Pecan file to execute', nargs='?')
    parser.add_argument('-i', '--interactive', help='Run Pecan in interactive mode (REPL)', required=False, action='store_true')
    parser.add_argument('-d', '--debug', help='Output debugging information', required=False, action='count')
    parser.add_argument('-q', '--quiet', help='Quiet mode', required=False, action='store_true')
    parser.add_argument('--no_opt', help='Turns off optimizations', required=False, action='store_true')
    parser.add_argument('--load_stdlib', help='Loads the standard library (from library/std.pn in your Pecan installation)', required=False, action='store_false')
    parser.add_argument('--generate', help='Enumerate true statements, argument is how many variables to use', type=int, required=False)

    args = parser.parse_args()

    if args.debug is None:
        args.debug = 0

    env = None
    if args.generate is not None:
        for pred in theorem_generator.gen_thms(args.generate):
            print(pred)
    elif args.file is not None:
        prog = program.load(args.file, quiet=args.quiet, debug=args.debug, load_stdlib=args.load_stdlib, no_opt=args.no_opt)
        env = prog.evaluate()
    elif not args.interactive:
        parser.print_help()

    if args.interactive:
        if env is None:
            prog = program.from_source('', quiet=args.quiet, debug=args.debug, load_stdlib=args.load_stdlib, no_opt=args.no_opt)
            env = prog.evaluate()

        run_repl(env)

if __name__ == '__main__':
    colorama.init()
    spot.setup()
    main()

