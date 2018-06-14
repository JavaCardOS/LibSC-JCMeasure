#coding:utf-8

from abc import ABC, abstractmethod
from pathlib import Path
import time
import logging
log = logging.getLogger("jcmeasure")

from .context import Context
from . import libsc as sc


class Action(ABC):
    """
    Base class of action.
    """

    @abstractmethod
    def run(self, ctx: Context) -> float:
        pass


class LoadAndInstall(Action):
    def __init__(self, json_file, cap_file):
        if Path(cap_file).is_absolute():
            self.__cap_file = cap_file
        else:
            self.__cap_file = str(Path(json_file).parent / cap_file)

    def run(self, ctx: Context) -> float:
        log.debug(f"load CAP and install applet: {self.__cap_file}")
        cap = sc.CapFile(self.__cap_file)
        sd = sc.SecurityDomain(ctx.reader)

        try:
            sd.remove(cap.pkg_aid)
        except sc.RspError:
            pass

        t = time.perf_counter()

        sd.load_cap(cap)
        sd.install_applet(cap.pkg_aid, cap.app_aids[0])
        return time.perf_counter() - t


class Remove(Action):
    def __init__(self, json_file, aid):
        self.__aid = aid

    def run(self, ctx: Context) -> float:
        log.debug(f"remove: {self.__aid}")
        sd = sc.SecurityDomain(ctx.reader)
        t = time.perf_counter()
        sd.remove(self.__aid)
        return time.perf_counter() - t


class LoadCap(Action):
    def __init__(self, json_file, cap_file):
        if Path(cap_file).is_absolute():
            self.__cap_file = cap_file
        else:
            self.__cap_file = str(Path(json_file).parent / cap_file)

    def run(self, ctx: Context) -> float:
        log.debug(f"load CAP file: {self.__cap_file}")
        cap = sc.CapFile(self.__cap_file)
        sd = sc.SecurityDomain(ctx.reader)
        try:
            sd.remove(cap.pkg_aid)
        except sc.RspError:
            pass

        t = time.perf_counter()
        sd.load_cap(cap)
        return time.perf_counter() - t


class InstallApplet(Action):
    def __init__(self, json_file, pkg_aid, app_aid):
        self.__pkg_aid = pkg_aid
        self.__app_aid = app_aid

    def run(self, ctx: Context) -> float:
        log.debug(f"install applet: {self.__pkg_aid}, {self.__app_aid}")
        sd = sc.SecurityDomain(ctx.reader)

        t = time.perf_counter()
        sd.install_applet(self.__pkg_aid, self.__app_aid)
        return time.perf_counter() - t


class Select(Action):
    def __init__(self, json_file, aid):
        self.__aid = sc.AID(aid)

    def run(self, ctx: Context) -> float:
        log.debug(f"select: {self.__aid}")
        apdu = sc.CmdAPDU("00a4040000")
        apdu.data = bytes(self.__aid)
        rsp = ctx.reader.transmit(apdu)
        return rsp.time


class SendAPDU(Action):
    def __init__(self, json_file, apdu):
        self.__apdu = apdu

    def run(self, ctx: Context) -> float:
        log.debug(f"send apdu: {self.__apdu}")
        rsp = ctx.reader.transmit(self.__apdu)
        return rsp.time


class Reset(Action):
    def __init__(self, json_file):
        pass

    def run(self, ctx: Context) -> float:
        log.debug("reset")
        t = time.perf_counter()
        ctx.reader.reset()
        return time.perf_counter() - t


class Script(Action):
    def __init__(self, json_file, actions):
        self.__actions = actions

    def run(self, ctx: Context) -> float:
        t = 0
        for action in self.__actions:
            t += action.run(ctx)
        return t


def build_action(json_file, arg):
    if isinstance(arg, list):
        actions = [build_action(json_file, val) for val in arg]
        return Script(json_file, actions)
    elif isinstance(arg, str):
        args = arg.split()
        try:
            cls = globals()[args[0]]
            if issubclass(cls, Action):
                return cls(json_file, *args[1:])
            else:
                raise ValueError(arg)
        except Exception:
            raise ValueError(arg)
    else:
        raise TypeError(f"{arg} should be str or list")


__all__ = ["build_action"]