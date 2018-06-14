#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
def bytes_to_str(bytes, lower=True, prefix='', suffix='', sep=' '):
    if not isinstance(bytes, str):
        raise TypeError("bytes must be a str.")
    l = []
    for c in bytes:
        if lower:
            l.append('%s%02x%s' % (prefix, ord(c), suffix))
        else:
            l.append('%s%02X%s' % (prefix, ord(c), suffix))
    return sep.join(l)


import re

_RE_MATCH = re.compile(r'^\s*((0[xX])?[a-fA-F0-9]{2}\s*)*\s*$')
_RE_GET_HEX = re.compile(r'[a-fA-F0-9]{2}')
def str_to_bytes(s):
    if not isinstance(s, str):
        raise TypeError("s must be a str or unicode")
    if _RE_MATCH.match(s):
        hexes = []
        for hexstr in _RE_GET_HEX.findall(s):
            hexes.append(chr(int(hexstr, 16)))
        return ''.join(hexes)
    else:
        raise ValueError("cannot convert to bytes from \"%s\"" % s)

def compile_package(package_name, srcdir, outdir, jcver, gpver, debug, more_apis):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    javaver = "1.5" if jcver != "221" else "1.2"
    libpath = os.path.join(os.path.dirname(__file__), "jclib")
    classpath = os.pathsep.join([libpath + "/jc" + jcver + "/api.jar",
                                 libpath + "/gp" + gpver + "/api.jar",
                                ] + (list(more_apis) if more_apis else []) + [outdir])
    sourcepath = os.path.join(srcdir, package_name.replace(".", os.sep))
    dbgflag = "-g" if debug else ""
    cmd = "javac -Xlint:-options -classpath {classpath} -target {javaver} -source {javaver} -d {outdir} {dbgflag} {sourcepath}/*.java".format(**locals())
    cmd = os.path.normpath(cmd)
    print(cmd)
    ret = os.system(cmd)
    if ret != 0:
        raise Exception("Compile package failed.")

def convert_package(package_info, classdir, outdir, jcver, gpver, debug, enableint, more_exps, map_exp):
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    libpath = os.path.join(os.path.dirname(__file__), "jclib")
    dbgflag = "-debug" if debug else ""
    intflag = "-i" if enableint else ""
    mapflag = "-exportmap" if map_exp else ""
    exppath = os.pathsep.join([libpath + "/jc" + jcver + "/api_export_files",
                               libpath + "/gp" + gpver + "/api_export_files",
                              ] + (list(more_exps) if more_exps else []) + [outdir])
    pkgname = package_info["name"]
    pkgaid = bytes_to_str(str_to_bytes(package_info["aid"]), prefix="0x", sep=":")
    pkgver = package_info["version"]
    appcmds = []
    for app in package_info.get("applets", []):
        appcmds.append("-applet %s %s" % (bytes_to_str(str_to_bytes(app["aid"]), prefix="0x", sep=":"), app["name"]))
    appcmds = " ".join(appcmds)
    cvtclass = "com.sun.javacard.converter.Converter"

    convert = "java -classpath {libpath}/jc{jcver}/converter.jar;{libpath}/jc{jcver}/offcardverifier.jar {cvtclass} -exportpath {exppath} -out JCA CAP EXP -classdir {classdir} -d {outdir} {mapflag} {intflag} {dbgflag} {appcmds} {pkgname} {pkgaid} {pkgver}".format(**locals())
    convert = os.path.normpath(convert)
    print(convert)
    ret = os.system(convert)
    if ret != 0:
        raise Exception("Convert package failed.")

def convert_jca(out_file, jca_file, jcver, gpver):
    cvtclass = "com.sun.javacard.jcasm.cap.Main"
    libpath = os.path.join(os.path.dirname(__file__), "jclib")
    convert = f"java -classpath {libpath}/jc{jcver}/converter.jar;{libpath}/jc{jcver}/offcardverifier.jar {cvtclass} -o {out_file} {jca_file}"
    print(convert)
    ret = os.system(convert)
    if ret != 0:
        raise Exception(("Convert jca failed."))
