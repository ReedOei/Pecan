#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

import os

# From: https://stackoverflow.com/a/6222692/1498618
def touch(fname):
    try:
        os.utime(fname, None)
    except OSError:
        with open(fname, 'a'):
            pass

