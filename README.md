# Pecan

[![Build Status](https://travis-ci.org/ReedOei/Pecan.svg?branch=master)](https://travis-ci.org/ReedOei/Pecan

Pecan is an automated theorem prover for Büchi automata, with additional features for making it easier to deal with expressing numbers in various numeration systems and working with automatic words.

## Installation

You will need Python 3.3 or higher.

Then, install [spot](https://spot.lrde.epita.fr/install.html), if you are on a Linux system, the `install-spot.sh` script may work for you:

```bash
bash install-spot.sh
```

Otherwise, follow the instructions on the spot website.

You will also need to install the libraries in `requirements.txt`:

```bash
# Use the appropriate line for your pip installation (if pip --version says 3.x, then you should be good; otherwise use/install pip3)
pip install -r requirements.txt
pip3 install -r requirements.txt
```

## Examples

Below `has_zeros` and `all_ones` are expressed as [LTL formula](https://en.wikipedia.org/wiki/Linear_temporal_logic).

```
has_zeros(a) := "!(Ga)"
all_ones(a) := "Ga"

prop_true() := forall x. has_zeros(x) => (not all_ones(x))
#assert_prop(true, prop_true)

prop_false() := exists x. has_zeros(x) & all_ones(x)
#assert_prop(false, prop_false)
```

## Configuration

The `PECAN_PATH` environment variable controls which paths are searched for files when importing/loading automata.
It should be a colon-separated or semicolon-separated list of paths, depending on your operating system (Linux/MacOs uses `:`, Windows uses `;`).

## Todo

- Plotting?
- Documentation

