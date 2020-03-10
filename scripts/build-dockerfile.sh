#!/usr/bin/env bash

set -ex

git rev-parse HEAD
date

dockerfile="./Dockerfile"

if [[ -n "$1" ]]; then
    dockerfile="$1"
fi

docker build -t "pecan-prover:latest" - < "$dockerfile"

