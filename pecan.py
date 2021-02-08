#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import argparse
import colorama
import readline
import os
import sys

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
                settings.log(0, lambda: str(prog))
                prog.include_with_restrictions(env)
                env = prog.evaluate()
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
    parser.add_argument('-d', '--debug', help='Output debugging information', required=False, action='count')
    parser.add_argument('-q', '--quiet', help='Quiet mode', required=False, action='store_true')
    parser.add_argument('--no-opt', help='Turns off optimizations', required=False, action='store_true')
    parser.add_argument('--min-opt', help='Set optimizations to minimal levels (only boolean and arithmetic optimizations).', required=False, action='store_true')
    parser.add_argument('--no-stdlib', help='Turns off the default behavior of loading the standard library (from library/std.pn in your Pecan installation)', required=False, action='store_false')
    parser.add_argument('--generate', help='Enumerate true statements, argument is how many variables to use', type=int, required=False)
    parser.add_argument('--heuristics', help='Use heuristics to determine how to simplify automata. This flag is typically useful with large automata (>10000 states), and can cause worse performance with smaller automata.', required=False, action='store_true')
    parser.add_argument('--extract-implications', help='Alternate mode of running a program involving going through each theorem, extracting the top-level implication that needs to be checked (if applicable).', required=False, action='store_true')
    parser.add_argument('--use-var-map', help='Use the var_map from the specified file and convert the main file to use the same var map (i.e., the argument corresponding to <file>)', required=False, type=str)
    parser.add_argument('--stats', help='Write out statistics about each predicate defined and theorem tested (i.e., in save_aut and assert_prop)', required=False, action='store_true')
    parser.add_argument('--output-hoa', help='Outputs encountered Buchi automata into the file', required=False, type=str, dest="output_hoa", metavar="HOA_FILE")

    args = parser.parse_args()

    settings.set_quiet(args.quiet)
    settings.set_opt_level(0 if args.no_opt else 1)
    settings.set_load_stdlib(args.no_stdlib)
    settings.set_use_heuristics(args.heuristics)
    settings.set_min_opt(args.min_opt)
    settings.set_extract_implications(args.extract_implications)
    settings.set_write_statistics(args.stats)
    settings.set_output_hoa(args.output_hoa)

    if args.debug is None:
        settings.set_debug_level(0)
    else:
        settings.set_debug_level(args.debug)

    if args.use_var_map is not None:
        if args.file is None:
            print('If --use-var-map is specified, you must also specify <file>!')
            exit(1)

        from pecan.tools.hoa_loader import load_hoa
        use_var_map_aut = load_hoa(args.use_var_map)
        main_file_aut = load_hoa(args.file)

        ap_subs = {}
        for v, aps in use_var_map_aut.get_var_map().items():
            for main_ap, new_ap in zip(main_file_aut.get_var_map().get(v, []), aps):
                ap_subs[main_ap] = new_ap

        s = main_file_aut.aut.to_str('hoa')
        for a,b in ap_subs.items():
            s = s.replace(a, b)
        print(s)

        # print(ap_subs)
        # main_file_aut = main_file_aut.ap_substitute(ap_subs)
        # print(main_file_aut.to_str())

        return

    env = None
    if args.generate is not None:
        for pred in theorem_generator.gen_thms(args.generate):
            print(pred)
    elif args.file is not None:
        try:
            prog = program.load(args.file)
            if not settings.get_extract_implications():
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
    # Increase a little bit (default is 1000) because Praline is very inefficient.
    sys.setrecursionlimit(2000)

    colorama.init()
    spot.setup()
    main()

