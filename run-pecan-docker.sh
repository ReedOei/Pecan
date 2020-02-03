#!/usr/bin/env bash

if ! docker inspect pecan-prover > /dev/null 2>&1; then
    bash build-dockerfile.sh
fi

docker run -it pecan-prover python3 /home/pecan/ReedOei/Pecan/pecan.py $@

