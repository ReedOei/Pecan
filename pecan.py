#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import argparse
import colorama
import readline
import os

from pecan.lang.lark.parser import UnexpectedToken

import spot

import pecan.tools.theorem_generator as theorem_generator
from pecan import program

from pecan.settings import settings

from pecan import utility

def run_repl(env):
    utility.touch(settings.get_history_file())
    readline.read_history_file(settings.get_history_file())

    while True:
        try:
            prog_str = input('> ').strip()

            if prog_str.lower() == 'exit':
                break

            if prog_str.startswith(':set'):
                parts = prog_str.split(' ')
                if len(parts) > 1:
                    if parts[1] == 'debug':
                        settings.set_debug_level(1 if settings.get_debug_level() <= 0 else 0)
            else:
                prog = program.from_source(prog_str)
                settings.log(0, prog)
                env = prog.evaluate(env)
        except KeyboardInterrupt:
            print('') # newline to go "below" the prompt
            print("Use 'exit' to exit Pecan.")
        except EOFError:
            print('exit')
            break
        except UnexpectedToken as e:
            print(e)
        except Exception as e:
            print('An exception occurred:', e)

    readline.write_history_file(settings.get_history_file())

def main():
    parser = argparse.ArgumentParser(description='An automated theorem prover for Büchi Automata')
    parser.add_argument('file', help='A Pecan file to execute', nargs='?')
    parser.add_argument('-i', '--interactive', help='Run Pecan in interactive mode (REPL)', required=False, action='store_true')
    parser.add_argument('-d', '--debug', help='Output debugging information', required=False, action='store_true')
    parser.add_argument('-q', '--quiet', help='Quiet mode', required=False, action='store_true')
    parser.add_argument('--no_opt', help='Turns off optimizations', required=False, action='store_true')
    parser.add_argument('--load_stdlib', help='Loads the standard library (from library/std.pn in your Pecan installation)', required=False, action='store_false')
    parser.add_argument('--generate', help='Enumerate true statements, argument is how many variables to use', type=int, required=False)

    args = parser.parse_args()

    if args.debug is None:
        settings.set_debug_level(0)
    else:
        settings.set_debug_level(args.debug)

    settings.set_quiet(args.quiet)
    settings.set_opt_level(0 if args.no_opt else 1)
    settings.set_load_stdlib(args.load_stdlib)

    env = None
    if args.generate is not None:
        for pred in theorem_generator.gen_thms(args.generate):
            print(pred)
    elif args.file is not None:
        try:
            prog = program.load(args.file)
            env = prog.evaluate()
        except UnexpectedToken as e:
            print(e)
            return None

    elif not args.interactive:
        parser.print_help()

    if args.interactive:
        if env is None:
            prog = program.from_source('')
            env = prog.evaluate()

        run_repl(env)

if __name__ == '__main__':
    colorama.init()
    spot.setup()
    main()

