#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

# This module provides an infrastructure for configuring Pecan
# All uses of various config options like debug mode, quiet mode, etc. are managed from here

import os

class Settings:
    def __init__(self):
        self.debug_level = 0
        self.quiet = False
        self.opt_level = 1
        self.load_stdlib = True
        self.pecan_path_var = 'PECAN_PATH'

    def get_pecan_path(self):
        if self.pecan_path_var in os.environ:
            return os.getenv(self.pecan_path_var).split(os.pathsep)
        else:
            return []

    def set_debug_level(self, level):
        assert level >= 0
        self.debug_level = level
        return self

    def get_debug_level(self):
        return self.debug_level

    def set_quiet(self, val):
        self.quiet = val
        return self

    def is_quiet(self):
        return self.quiet

    def set_opt_level(self, level):
        assert level >= 0
        self.opt_level = level
        return self

    def get_opt_level(self):
        return self.opt_level

    def opt_enabled(self):
        return self.opt_level > 0

    def set_load_stdlib(self, val):
        self.load_stdlib = val
        return self

    def should_load_stdlib(self):
        return self.load_stdlib

    def log(self, level, msg=None):
        if msg is None:
            msg = level
            if not self.is_quiet():
                print(msg)
        elif self.get_debug_level() > level:
            print(msg)

settings = Settings()

