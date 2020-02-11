#!/usr/bin/env bash

set -ex

echo "$(git rev-parse HEAD)"
date

SPOT_VERSION="2.8.5"
PYTHON_VERSION="3.6"

# download/uncompress spot

if ! python3 -c "import spot"; then
    if [[ ! -d "spot-$SPOT_VERSION" ]]; then
        curl -o "spot-$SPOT_VERSION.tar.gz" "http://www.lrde.epita.fr/dload/spot/spot-$SPOT_VERSION.tar.gz"
        gunzip "spot-$SPOT_VERSION.tar.gz"
        tar xvf "spot-$SPOT_VERSION.tar"
    else
        echo "Skipped downloading spot, directory already exists"
    fi

    cd "spot-$SPOT_VERSION"

    ./configure --prefix ~/.local
    make
    sudo make install
else
    echo "Skipped installing spot---already found."
fi

