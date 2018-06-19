#coding:utf-8

import time
from .measurecase import MeasureCase
import logging
log = logging.getLogger("jcmeasure")


class Reporter:
    """
    A simple text reporter.
    """
    def __init__(self):
        self.__infos = [('Name', 'Result', "Description")]

    def report_case(self, case: MeasureCase, result: float):
        log.debug(f"{case.name}: {result} {case.unit}")
        self.__infos.append((case.name, f"{result:.02f} {case.unit}",
                             case.description))

    def report_failure(self, case: MeasureCase):
        self.__infos.append((case.name, "failed", case.description))
        log.debug(f"{case.name} failed")

    def gen_report(self, file_name):
        with open(file_name, "w") as f:
            for info in self.__infos:
                print(f"{info[0]:<20s}    {info[1]:<30s}    {info[2]}", file=f)