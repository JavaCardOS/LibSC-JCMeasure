#coding:utf-8

import time
import sys
import logging
log = logging.getLogger("jcmeasure")

from pathlib import Path

from .context import Context
from .measurecase import MeasureCase
from .action import *
from .reporter import Reporter
from . import libsc


def load_measure_cases():
    tests = Path("./tests")
    for json_file in tests.glob("**/*.json"):
        yield MeasureCase.from_json(json_file)


class Driver:
    def __init__(self, config_file=None):
        self.__cases = list(load_measure_cases())
        log.debug(f"Driver inited, case count: {len(self.__cases)}.")

    def __parse_config(self, config_file):
        pass

    def __prepare_context(self):
        return Context(libsc.PCSCReader(), Reporter())

    def test(self):
        log.debug("prepare to test.")
        ctx = self.__prepare_context()
        try:
            # T=0 is better for measure speed because its wtx is short
            ctx.reader.open(protocol="T=0")
        except Exception:
            ctx.reader.open(protocol="auto")

        try:
            for case in self.__cases:
                assert isinstance(case, MeasureCase)
                try:
                    case.test(ctx)
                except Exception as e:
                    log.exception(e)
        finally:
            ctx.reader.close()
            ctx.reporter.gen_report(
                f"report_{time.strftime('%Y%m%d%H%M%S')}.txt")


def parse_cmdline():
    import sys
    import argparse

    parser = argparse.ArgumentParser(prog="jcmeasure")
    parser.add_argument(
        "--config", "-c", default=None, help="set config file.")
    parser.add_argument(
        "--list", "-l", default=None, help="set measure list file.")
    return parser.parse_args(sys.argv[1:])


def main():
    formatter = logging.Formatter(
        fmt=
        "%(color)s[%(name)s %(asctime)s %(levelname)s]%(end_color)s %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S')
    log.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '[%(name)s %(asctime)-15s - %(levelname)s] %(message)s')
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    log.addHandler(console)

    log2 = logging.getLogger("libsc")
    log2.setLevel(logging.INFO)
    log2.addHandler(console)

    ns = parse_cmdline()
    drv = Driver(ns.config)
    drv.test()
