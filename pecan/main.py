#!/usr/bin/env

import spot
import sys

from pecan.lang.parser import pecan_parser

def main(args):
    pass

print(pecan_parser.parse('x = alpha'))

if __name__ == '__main__':
    spot.setup()
    main(sys.argv)

