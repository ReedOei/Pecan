#!/usr/bin/env python3.6
# -*- coding=utf-8 -*-

# This module provides an infrastructure for configuring Pecan
# All uses of various config options like debug mode, quiet mode, etc. are managed from here

import os

from pathlib import Path

class Settings:
    def __init__(self):
        self.debug_level = 0
        self.quiet = False
        self.opt_level = 1
        self.load_stdlib = True
        self.pecan_path_var = 'PECAN_PATH'
        self.history_file = 'pecan_history'
        self.simplication_level = 1
        self.should_use_heuristics = False
        self.only_min_opt = False
        self.extract_implications = False
        self.write_statistics = False

        self.stdlib_prog = None

    def should_write_statistics(self):
        return self.write_statistics

    def set_write_statistics(self, write_statistics):
        self.write_statistics = write_statistics
        return self

    def get_extract_implications(self):
        return self.extract_implications

    def set_extract_implications(self, b):
        self.extract_implications = b
        return self

    def min_opt(self):
        return self.only_min_opt

    def set_min_opt(self, min_opt):
        self.only_min_opt = min_opt
        return self

    def get_simplication_level(self):
        return self.simplication_level

    def set_simplification_level(self, new_level):
        self.simplication_level = new_level
        return self

    def get_history_file(self):
        return Path.home() / self.history_file

    def set_history_file(self, filename):
        self.history_file = filename
        return self

    def get_pecan_path(self):
        if self.pecan_path_var in os.environ:
            return os.getenv(self.pecan_path_var).split(os.pathsep)
        else:
            return []

    def set_debug_level(self, level):
        self.debug_level = max(0,level)
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

    def set_use_heuristics(self, use_heuristics):
        self.should_use_heuristics = use_heuristics
        return self

    def use_heuristics(self):
        return self.should_use_heuristics

    def set_load_stdlib(self, val):
        self.load_stdlib = val
        return self

    def should_load_stdlib(self):
        return self.load_stdlib

    def log(self, level, msg=None):
        if msg is None:
            msg = level
            if not self.is_quiet():
                print(msg())
        elif self.get_debug_level() > level:
            print(msg())

    def include_stdlib(self, prog, loader, args, kwargs):
        if self.should_load_stdlib():
            orig_debug_level = self.get_debug_level()
            before = self.should_load_stdlib()
            before_quiet = self.is_quiet()
            try:
                # Don't want to load stdlib while loading stdlib
                self.set_load_stdlib(False)
                self.set_quiet(True)
                self.set_debug_level(orig_debug_level - 1)

                if self.stdlib_prog is None:
                    self.stdlib_prog = loader(prog.locate_file('std.pn'), *args, **kwargs)
                    self.stdlib_prog.evaluate()

                prog.include(self.stdlib_prog)
            finally:
                self.set_load_stdlib(before)
                self.set_quiet(before_quiet)
                self.set_debug_level(orig_debug_level)

        return prog

settings = Settings()

