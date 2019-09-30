#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import argparse
import spot

from pecan.lang.parser import pecan_parser

def main():
    parser = argparse.ArgumentParser(description='An automated theorem prover for Büchi Automata')
    parser.add_argument('-f', '--file', help='A Pecan file to execute')
    parser.add_argument('-i', '--interactive', help='Run Pecan in interactive mode (REPL)')

    args = parser.parse_args()

if __name__ == '__main__':
    spot.setup()
    main()

