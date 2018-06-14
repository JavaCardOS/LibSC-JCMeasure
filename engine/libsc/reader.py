#coding:utf-8
"""
Smart Card Reader.
"""

from abc import ABC, abstractmethod
import ctypes as ct
import time
import logging
from functools import wraps

log = logging.getLogger("libsc")

from .base import *


class ReaderError(Exception):
    """
    Reader exception.
    """
    pass


class Reader(ABC):
    """
    Base class for smart card reader.
    """

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def is_open(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def get_protocol(self):
        pass

    @abstractmethod
    def get_atr(self):
        pass

    @abstractmethod
    def transmit(self, apdu):
        pass


def auto_get_rsp(func):
    @wraps(func)
    def transmit(reader: Reader, apdu):
        if reader.get_protocol() != 'T=0':
            return func(reader, apdu)

        # only get response for T=0
        datas = []
        time_used = 0
        while 1:
            rsp = func(reader, apdu)
            if rsp.sw1 == b'\x61':
                datas.append(rsp.data)
                time_used += rsp.time
                apdu = b'\x00\xc0\x00\x00' + rsp.sw2

            elif rsp.sw1 == b'\x6c':
                datas.append(rsp.data)
                time_used += rsp.time
                apdu = CmdAPDU(apdu)
                apdu.le = rsp.sw2

            else:
                return RspAPDU(b''.join(datas) + bytes(rsp),
                               rsp.time + time_used)

    return transmit


_mod = ct.windll.winscard


def _scard_check_ret(ret, func, args):
    if ret != 0:
        error = ct.FormatError(ret)
        raise ReaderError(error)
    else:
        return ret


_SCardEstablishContext = _mod.SCardEstablishContext
_SCardEstablishContext.errcheck = _scard_check_ret

_SCardListReaders = _mod.SCardListReadersW
_SCardListReaders.errcheck = _scard_check_ret

_SCardReleaseContext = _mod.SCardReleaseContext
_SCardReleaseContext.errcheck = _scard_check_ret

_SCardConnect = _mod.SCardConnectW
_SCardConnect.errcheck = _scard_check_ret

_SCardStatus = _mod.SCardStatusW
_SCardStatus.errcheck = _scard_check_ret

_SCardDisconnect = _mod.SCardDisconnect
_SCardDisconnect.errcheck = _scard_check_ret

_SCardTransmit = _mod.SCardTransmit
_SCardTransmit.errcheck = _scard_check_ret

_SCardReconnect = _mod.SCardReconnect
_SCardReconnect.errcheck = _scard_check_ret

_SCardGetStatusChange = _mod.SCardGetStatusChangeW


class PCSCReader(Reader):
    """
    PC/SC smart card reader.
    """

    def __init__(self, name=None, shared=False):
        if name is None:
            # get the reader name
            first = None
            for name, card_inside in list_pcsc_readers():
                if not first:
                    first = name
                if card_inside:
                    self.__reader = name
                    break
            else:
                if first:
                    self.__reader = first
                else:
                    raise ValueError("No PCSC reader found")
        else:
            self.__reader = str(name)

        self.__context = ct.c_void_p(0)
        self.__handle = ct.c_ulong(0)
        self.__pro = None
        self.__shared = bool(shared)

    def __repr__(self):
        return f"PCSCReader(name='{self.__reader}', shared={self.__shared})"

    def open(self, protocol="auto"):
        if isinstance(protocol, str):
            pro = protocol.lower()
            if pro in ("t0", "t=0"):
                pro_val = 1  # T=0
            elif pro in ("t1", "t=1"):
                pro_val = 2  # T=1
            elif pro == "auto":
                pro_val = 3  # T=0 | T=1
            else:
                raise ValueError(f"Protocol {pro} not supported.")
        else:
            raise ValueError(f"Protocol {pro} not supported.")

        if self.is_open():
            raise ReaderError("Smart card already connected.")

        _SCardEstablishContext(0, 0, 0, ct.byref(self.__context))

        dwActivePro = ct.c_ulong(0)
        # connect to the card
        _SCardConnect(self.__context, self.__reader, 2 if self.__shared else 1,
                      pro_val, ct.byref(self.__handle), ct.byref(dwActivePro))

        if dwActivePro.value == 1:
            self.__pro = "T=0"
        else:
            self.__pro = "T=1"
        log.info(
            f"{self} open, protocol: {self.get_protocol()}, ATR: {self.get_atr().hex()}"
        )

    def is_open(self):
        return self.__handle.value != 0

    def close(self):
        """
        Close connection.
        """
        # define SCARD_LEAVE_CARD      0 // Don't do anything special on close
        # define SCARD_RESET_CARD      1 // Reset the card on close
        # define SCARD_UNPOWER_CARD    2 // Power down the card on close
        # define SCARD_EJECT_CARD      3 // Eject the card on close
        if self.is_open():
            _SCardDisconnect(self.__handle, 2)
            self.__handle = ct.c_ulong(0)
            _SCardReleaseContext(self.__context)
            self.__context = ct.c_void_p(0)
            self.__pro = None
            log.info(f"{self} close")

    def reset(self, protocol=None, cold=True):
        if not self.is_open():
            raise ReaderError("Smart card is already disconnected.")

        if protocol is None:
            protocol = self.__pro

        if isinstance(protocol, str):
            pro = protocol.lower()
            if pro in ("t0", "t=0"):
                pro_val = 1  # T=0
            elif pro in ("t1", "t=1"):
                pro_val = 2  # T=1
            elif pro == "auto":
                pro_val = 3  # T=0 | T=1
            else:
                raise ValueError(f"Protocol {pro} not supported.")
        else:
            raise ValueError(f"Protocol {pro} not supported.")

        dwActivePro = ct.c_ulong(0)
        _SCardReconnect(self.__handle, 2 if self.__shared else 1, pro_val, 2
                        if cold else 1, ct.byref(dwActivePro))

        if dwActivePro.value == 1:
            self.__pro = "T=0"
        else:
            self.__pro = "T=1"
        log.info(
            f"{self} reset, protocol: {self.get_protocol()}, ATR: {self.get_atr().hex()}"
        )

    def get_protocol(self):
        if not self.is_open():
            raise ReaderError("Smart card is not connected.")
        return self.__pro

    def get_atr(self):
        if not self.is_open():
            raise ReaderError("Smart card is not connected.")

        atr = ct.create_string_buffer(40)
        atrlen = ct.c_ulong(40)
        _SCardStatus(self.__handle, 0, 0, 0, 0, atr, ct.byref(atrlen))
        return atr[:atrlen.value]

    @auto_get_rsp
    def transmit(self, apdu):
        if not self.is_open():
            raise ReaderError("Smart card is not connected.")

        if isinstance(apdu, str):
            apdu_data = bytes.fromhex(apdu)
        elif isinstance(apdu, CmdAPDU):
            apdu_data = bytes(apdu)
        elif isinstance(apdu, bytes):
            apdu_data = apdu
        else:
            raise TypeError(apdu)

        recv = ct.create_string_buffer(65538)
        recvLen = ct.c_long(65538)
        length = len(apdu_data)

        log.info(f"send: {apdu_data.hex()}")

        if self.get_protocol() == "T=0":
            propci = _mod.g_rgSCardT0Pci
        else:
            propci = _mod.g_rgSCardT1Pci

        t1 = time.perf_counter()
        _SCardTransmit(self.__handle, propci, apdu_data, length, 0, recv,
                       ct.byref(recvLen))
        t2 = time.perf_counter()
        rsp = RspAPDU(recv[:recvLen.value], t2 - t1)
        log.info(f"recv: {rsp} in {rsp.time*1000:.02f} ms")
        return rsp


class _SCARD_READERSTATE(ct.Structure):
    _fields_ = [
        ("szReader", ct.c_wchar_p),
        ("pvUserData", ct.c_void_p),
        ("dwCurrentState", ct.c_uint),
        ("dwEventState", ct.c_uint),
        ("cbAtr", ct.c_uint),
        ("rgbAtr", ct.c_byte * 36),
    ]


def list_pcsc_readers():
    """
    A generator to list all PCSC readers. yield (reader_name, is_card_in_reader) for each loop, for example: ("Reader 1", True), ("Reader 2", False) ...
    """
    readers = []
    context = ct.c_void_p(0)
    try:
        _SCardEstablishContext(0, 0, 0, ct.byref(context))
        buff = ct.create_unicode_buffer(2048)
        cch = ct.c_ulong(2048)
        _SCardListReaders(context, 0, ct.byref(buff), ct.byref(cch))
        readers = buff[:cch.value - 2].split('\x00')
        for reader in readers:
            state = _SCARD_READERSTATE(0, 0, 0, 0, 0)
            state.szReader = str(reader)
            state.pvUserData = 0
            state.dwCurrentState = 0
            state.dwEventState = 0
            state.cbAtr = 0
            ret = _SCardGetStatusChange(context, 0, ct.byref(state), 1)
            yield (reader, ret == 0 and (state.dwEventState & 0x0020) != 0)
    finally:
        _SCardReleaseContext(context)


__all__ = [
    "Reader",
    "PCSCReader",
    "list_pcsc_readers",
]