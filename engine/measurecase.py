#coding:utf-8
"""
Test case and group.
"""

import json
import logging
log = logging.getLogger("jcmeasure")

from .context import Context
from .action import build_action, Action


class MeasureCase:
    """
    Test case.
    """

    def __init__(self, name: str, description: str, round: int, result_func,
                 unit: str, setup: Action, teardown: Action, adjust: Action,
                 test: Action):

        self.name = name
        self.description = description
        self.round = round
        self.result_func = eval(result_func)
        self.unit = unit
        self.__setup = setup
        self.__teardown = teardown
        self.__adjust = adjust
        self.__test = test

    @classmethod
    def from_json(cls, json_file):
        val = json.loads(open(json_file).read())
        if not isinstance(val, dict):
            raise ValueError(val)

        name = val.get("name", json_file)
        description = val.get("description", "")
        round = val.get("round", 10)
        result_func = val.get("result", "lambda t: 1.0/t")
        unit = val.get("unit", "INS/S")

        setup = build_action(json_file, val["setup"])
        teardown = build_action(json_file, val["teardown"])
        adjust = build_action(json_file, val["adjust"])
        test = build_action(json_file, val["test"])

        return cls(name, description, round, result_func, unit, setup,
                   teardown, adjust, test)

    def test(self, ctx: Context):
        log.debug(f"run MeasureCase {self.name}")

        try:
            self.__setup.run(ctx)
        except Exception as e:
            log.error(f"setup failed. {e}")
            log.exception(e)

        try:
            t1 = [self.__adjust.run(ctx) for i in range(self.round)]
        except Exception as e:
            log.error(f"adjust failed. {e}")
            log.exception(e)
            t1 = None

        t2 = None
        if t1 is not None:
            try:
                t2 = [self.__test.run(ctx) for i in range(self.round)]
            except Exception as e:
                log.error(f"test failed. {e}")
                log.exception(e)

        if t1 is not None and t2 is not None:
            result = self.result_func(min(t2) - min(t1))
            ctx.reporter.report_case(self, result)
        else:
            ctx.reporter.report_failure(self)

        try:
            self.__teardown.run(ctx)
        except Exception as e:
            log.error(f"teardown failed. {e}")
            log.exception(e)
