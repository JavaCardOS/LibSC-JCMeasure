#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
This package is used to provide Java Card applet builder for scons
'''

__version__ = "1.1.2"


def gen_caps(packages,
             srcdir="src",
             outdir="bin",
             jcver="222",
             gpver="211",
             debug=1,
             enableint=1,
             more_apis=None,
             more_exps=None,
             map_exp=0):
    from . import jcscons
    return jcscons.gen_caps(packages, srcdir, outdir, jcver, gpver, debug,
                            enableint, more_apis, more_exps, map_exp)


def convert_jca(cap_file, jca_file, jcver="222", gpver="211"):
    from . import jcscons
    return jcscons.convert_jca(cap_file, jca_file, jcver, gpver)
