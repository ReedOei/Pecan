#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import argparse
import spot

from pecan.lang.parser import pecan_parser

def run_repl(debug, env):
    while True:
        prog_str = input('> ')
        prog = pecan_parser.parse(prog_str)

        if debug:
            print(prog)

        env = prog.evaluate(env)

def main():
    parser = argparse.ArgumentParser(description='An automated theorem prover for Büchi Automata')
    parser.add_argument('file', help='A Pecan file to execute')
    parser.add_argument('-i', '--interactive', help='Run Pecan in interactive mode (REPL)', required=False, action='store_true')
    parser.add_argument('-d', '--debug', help='Output debugging information', required=False, action='store_true')

    args = parser.parse_args()

    if args.file is not None:
        with open(args.file, 'r') as f:
            prog = pecan_parser.parse(f.read())

        if args.debug:
            print(prog)

        env = prog.evaluate()

        if args.interactive:
            run_repl(args.debug, env)

if __name__ == '__main__':
    spot.setup()
    main()

