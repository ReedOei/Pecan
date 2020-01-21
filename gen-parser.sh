#!/usr/bin/env bash

grammar_file="$1"
output_file="$2"

if [[ -z "$grammar_file" ]]; then
    grammar_file="pecan/lang/lark/pecan_grammar.lark"
fi

if [[ -z "$output_file" ]]; then
    output_file="pecan/lang/lark/parser.py"
fi

python3 -m lark.tools.standalone "$grammar_file" > "$output_file"

echo "Grammar size (lines, words, characters): "
python3 -m lark.tools.standalone "$grammar_file" | wc

