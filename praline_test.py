import sys
from lark import Lark

from pecan.lang.parser import pecan_parser

with open(sys.argv[1], 'r') as f:
    print(pecan_parser.parse(f.read()))

