#!/usr/bin/env bash

set -ex

echo "$(git rev-parse HEAD)"
date

docker build -t "pecan-prover:latest" - < "./Dockerfile"

