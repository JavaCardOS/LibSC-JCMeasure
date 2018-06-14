#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import SCons.Builder
import SCons.Environment
from . import jcbuild

def build_cap(target, source, env):
    packages, srcdir, outdir, jcver, gpver, debug, enableint, more_apis, more_exps, map_exp = env["JCARGS"]
    p = os.path.normpath(os.path.dirname(str(source[0])))
    for pkg in packages:
        if p.endswith(pkg["name"].replace(".", os.path.sep)):
            _srcdir = p[:-len(pkg["name"]) - 1]
            if not _srcdir.endswith(os.path.normcase(srcdir)):
                continue
            _outdir = os.path.dirname(os.path.dirname(str(target[0])))[:-len(pkg["name"])-1]
            jcbuild.compile_package(pkg["name"], _srcdir, _outdir, jcver, gpver, debug, more_apis)
            jcbuild.convert_package(pkg, _outdir,_outdir, jcver, gpver, debug, enableint, more_exps, map_exp)

def gen_caps(packages, srcdir, outdir, jcver, gpver, debug, enableint, more_apis, more_exps, map_exp):
    env = SCons.Environment.Environment(
        ENV = os.environ,
        BUILDERS = {"BuildCap" : SCons.Builder.Builder(action = build_cap)}
        )
    env["JCARGS"] = [packages, srcdir, outdir, jcver, gpver, debug, enableint, more_apis, more_exps, map_exp]
    allcaps = []
    for pkg in packages:
        pkgdir = pkg["name"].replace(".", os.path.sep)
        sources = [os.path.join(srcdir, pkgdir, fname) for fname in os.listdir(os.path.join(srcdir, pkgdir)) if fname.endswith(".java")]
        classes = [os.path.join(outdir, pkgdir, fname[:-5] + ".class") for fname in os.listdir(os.path.join(srcdir, pkgdir)) if fname.endswith(".java")]
        if not sources:
            continue

        capfile = os.path.join(outdir, pkgdir, "javacard", os.path.basename(pkgdir) + ".cap")
        cap = env.BuildCap(capfile, sources)
        env.Clean(cap, [classes, capfile[-4] + ".exp", capfile[-4] + ".jca"])
        allcaps += cap

        # find dependencies
        importpkgs = []
        for srcname in sources:
            importpkgs += re.findall(r"import ([^;]+)\.(?:\*|\w+);", open(srcname).read())
        importpkgs = list(set(importpkgs))
        for _pkg in packages:
            if _pkg["name"] in importpkgs and _pkg != pkg:
                env.Depends(cap, os.path.join(outdir, _pkg["name"].replace(".", os.path.sep), "javacard", _pkg["name"].split(".")[-1] + ".cap"))
    env.Clean(allcaps, outdir)
    return allcaps

def do_convert_jca(target, source, env):
    jcver, gpver = env["JCARGS"]
    jcbuild.convert_jca(str(target[0]), str(source[0]), jcver, gpver)

def convert_jca(cap_file, jca_file, jcver, gpver):
    env = SCons.Environment.Environment(
        ENV = os.environ,
        BUILDERS = {"ConvertJca" : SCons.Builder.Builder(action = do_convert_jca)}
        )
    env["JCARGS"] = [jcver, gpver]
    cap = env.ConvertJca(cap_file, jca_file)
    return cap
