# Pecan

[![Build Status](https://travis-ci.org/ReedOei/Pecan.svg?branch=master)](https://travis-ci.org/ReedOei/Pecan)

Pecan is an automated theorem prover for Büchi automata, with additional features for making it easier to deal with expressing numbers in various numeration systems and working with automatic words.

You can try Pecan online! Just go to [http://reedoei.com/pecan](http://reedoei.com/pecan).

## Installation

NOTE: You can also use Docker (see below), if you have it.

You will need Python 3.6 or higher.

Then, install [spot](https://spot.lrde.epita.fr/install.html); if you are on a Linux-y system (hopefully including MacOS), the `install-spot.sh` script in the `scripts/` directory of this repository should work for you:

```bash
bash scripts/install-spot.sh
```

Otherwise, follow the instructions on the spot website.

You will also need to install the libraries in `requirements.txt`:

```bash
# Use the appropriate line for your pip installation (if pip --version says 3.x, then you should be good; otherwise use/install pip3)
pip install -r requirements.txt
pip3 install -r requirements.txt
```

Then you can run Pecan files (`*.pn`) by:
```bash
python3 pecan.py FILENAME
```

or start interactive mode via:
```bash
python3 pecan.py -i
```

You can also add the `bin/` directory of this repository to your `PATH`, and the simply use `pecan FILENAME` or `pecan -i`.
To do so, add the following to your `.bashrc` (or whatever your operating system uses):
```bash
export PATH=/path/to/Pecan/bin:$PATH
```

### Using Docker

If you have Docker, you can run Pecan with:

```bash
./pecan-docker OPTIONS
```

This will automatically build the image if you don't have it already.

## Examples

Below `has_zeros` and `all_ones` are expressed as [LTL formula](https://en.wikipedia.org/wiki/Linear_temporal_logic).

```
has_zeros(a) := "!(Ga)"
all_ones(a) := "Ga"

Prove that {
    forall x. if has_zeros(x) then !all_ones(x)
}.

Prove that {
    !(exists x. has_zeros(x) & all_ones(x))
}.
```

Below we prove basic properties of addition (specifically, binary addition), see ([here](https://github.com/ReedOei/Pecan/blob/master/examples/arith_props.pn)):
```
Restrict x, y, z are nat.

Theorem ("Zero is the additive identity", {
    forall x. x + 0 = x
}).

Theorem ("Addition is commutative", {
    forall x,y. x + y = y + x
}).

Theorem ("Addition is associative", {
    forall x,y,z. x + (y + z) = (x + y) + z
}).
```

Running it gives:
```bash
$ python3 pecan.py examples/arith_props.pn
[INFO] Checking if Zero is the additive identity is true.
Zero is the additive identity is true.
[INFO] Checking if Addition is commutative is true.
Addition is commutative is true.
[INFO] Checking if Addition is associative is true.
Addition is associative is true.
```

## Configuration

The `PECAN_PATH` environment variable controls which paths are searched for files when importing/loading automata.
It should be a colon-separated or semicolon-separated list of paths, depending on your operating system (Linux/MacOs uses `:`, Windows uses `;`).

## Editor Setup

Currently, the only supported editor is Vim, via a syntax file (`pecan.vim`) in this repository.

