#!/usr/bin/env bash

set -ex

echo "$(git rev-parse HEAD)"
date

SPOT_VERSION="2.8.1"
PYTHON_VERSION="3.6"

# download/uncompress spot
curl -o "spot-$SPOT_VERSION.tar.gz" "http://www.lrde.epita.fr/dload/spot/spot-$SPOT_VERSION.tar.gz"
gunzip "spot-$SPOT_VERSION.tar.gz"
tar xvf "spot-$SPOT_VERSION.tar"
cd "spot-$SPOT_VERSION"

./configure --prefix /usr
make
sudo make install
echo "export PYTHONPATH=/usr/lib/python$PYTHON_VERSION/site-packages:$PYTHONPATH" >> "$HOME/.bashrc"

