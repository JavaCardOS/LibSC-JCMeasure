# coding:utf-8
"""
APDU command and response class.
"""

import struct


class CmdAPDU:
    """
    Command APDU.
    """

    CASE1 = 1
    CASE2 = 2
    CASE3 = 3
    CASE4 = 4
    CASE2E = 5
    CASE3E = 6
    CASE4E = 7

    def __init__(self, val=None):
        if val is None:
            self.__fields = [
                b"\x00", b"\x00", b"\x00", b"\x00", b"", b"", b"\x00"
            ]
        elif isinstance(val, CmdAPDU):
            self.__fields = [
                val.cla, val.ins, val.p1, val.p2, val.lc, val.data, val.le
            ]
        elif isinstance(val, bytes):
            self.__parse(val)
        elif isinstance(val, str):
            self.__parse(bytes.fromhex(val))
        else:
            self.__parse(bytes(val))

    def __parse(self, apdu):
        data_len = len(apdu)
        if data_len < 4:
            raise ValueError(
                "The length of command apdu bytes must be larger than 4.")

        self.__fields = [
            apdu[0:1], apdu[1:2], apdu[2:3], apdu[3:4], b"", b"", b""
        ]

        if data_len == 4:  # case 1
            pass
        elif data_len == 5:  # case 2
            self.__fields[6] = apdu[4:5]
        elif apdu[4] != 0 and (apdu[4]) + 5 == data_len:  # case 3
            self.__fields[4] = apdu[4:5]
            self.__fields[5] = apdu[5:]
        elif apdu[4] != 0 and (apdu[4]) + 6 == data_len:  # case 4
            self.__fields[4] = apdu[4:5]
            self.__fields[5] = apdu[5:-1]
            self.__fields[6] = apdu[-1:]
        elif apdu[4] == 0 and data_len == 7:  # case 2E
            self.__fields[6] = apdu[-2:]
        # case 3E
        elif data_len > 7 and apdu[4] == 0 and (apdu[5]) * 256 + (
                apdu[6]) + 7 == data_len:
            self.__fields[4] = apdu[4:7]
            self.__fields[5] = apdu[7:]
        # case 4E
        elif data_len > 9 and apdu[4] == 0 and (apdu[5]) * 256 + (
                apdu[6]) + 9 == data_len:
            self.__fields[4] = apdu[4:7]
            self.__fields[5] = apdu[7:-2]
            self.__fields[6] = apdu[-2:]
        else:
            raise ValueError("The command apdu is not correct.")

    def __bytes__(self):
        if not self.lc and len(self.le) == 2:
            # for CASE2E, P3 should be 00 to indicate extended APDU
            return b''.join(self.__fields[0:4] + [b"\x00"] + self.__fields[5:])
        else:
            return b''.join(self.__fields)

    def __str__(self):
        return bytes(self).hex()

    def __repr__(self):
        return f"CmdAPDU('{self}')"

    def __eq__(self, val):
        if isinstance(val, bytes):
            return bytes(self) == val
        elif isinstance(val, str):
            return bytes.fromhex(val) == bytes(self)
        elif isinstance(val, CmdAPDU):
            return bytes(self) == bytes(val)
        else:
            return False

    @property
    def case(self):
        """
        The case of APDU, read only property.
        """
        lc = self.lc
        le = self.le
        if not self.is_extended():
            if not lc and not le:
                return self.CASE1
            elif not lc and le:
                return self.CASE2
            elif lc and not le:
                return self.CASE3
            else:
                return self.CASE4
        else:
            if not lc and le:
                return self.CASE2E
            elif lc and not le:
                return self.CASE3E
            else:
                assert lc and le
                return self.CASE4E

    def __update_field(self, i, name, val):
        assert i < 4
        if isinstance(val, bytes):
            if len(val) != 1:
                raise ValueError("Length of `%s` is not correct." % name)
            self.__fields[i] = val
        elif isinstance(val, str):
            val = bytes.fromhex(val)
            if len(val) != 1:
                raise ValueError("Length of `%s` is not correct." % name)
            self.__fields[i] = val
        elif isinstance(val, int):
            if val < 0 or val > 255:
                raise ValueError("`%s` must in range 0 ~ 255" % name)
            self.__fields[i] = bytes([val])
        else:
            raise TypeError(
                "Type of `%s` must be `bytes`, `str` or `int`" % name)

    @property
    def cla(self):
        """
        Getter for CLA of APDU.
        """
        return self.__fields[0]

    @cla.setter
    def cla(self, cla):
        """
        Setter for CLA of APDU.
        """
        self.__update_field(0, "cla", cla)

    @property
    def ins(self):
        """
        Getter for INS of APDU.
        """
        return self.__fields[1]

    @ins.setter
    def ins(self, ins):
        """
        Setter for INS of APDU.
        """
        self.__update_field(1, "ins", ins)

    @property
    def p1(self):
        """
        Getter for P1 of APDU.
        """
        return self.__fields[2]

    @p1.setter
    def p1(self, p1):
        """
        Setter for P1 of APDU.
        """
        return self.__update_field(2, "p1", p1)

    @property
    def p2(self):
        """
        Getter for P2 of APDU.
        """
        return self.__fields[3]

    @p2.setter
    def p2(self, p2):
        """
        Setter for P2 of APDU.
        """
        return self.__update_field(3, "p2", p2)

    @property
    def lc(self):
        """
        Getter for LC of APDU. LC is changed when data field of APDU changed.
        """
        return self.__fields[4]

    @property
    def data(self):
        """
        Getter for data field of APDU.
        """
        return self.__fields[5]

    @data.setter
    def data(self, data):
        """
        Setter for data field of APDU.
        """
        if isinstance(data, str):
            data = bytes.fromhex(data)
        if not isinstance(data, bytes):
            raise TypeError("Type of `data` must be `bytes` or `str`")
        self.__fields[5] = data
        data_len = len(data)
        if len(data) == 0:
            self.__fields[4] = b""  # lc
        else:
            if len(self.le) == 2 or data_len > 255:  # extended apdu
                self.__fields[4] = struct.pack(">BH", 0, data_len)
                if len(self.le) == 1:
                    self.__fields[6] = b"\x00" + self.__fields[6]
            else:
                self.__fields[4] = bytes([data_len])

    @property
    def le(self):
        """
        Getter for LE of APDU.
        """
        return self.__fields[6]

    @le.setter
    def le(self, le):
        """
        Setter for LE of APDU.
        """
        if isinstance(le, str):
            le = bytes.fromhex(le)

        if isinstance(le, bytes):
            if len(le) not in (0, 1, 2):
                raise ValueError("Length of `le` must be 0, 1 or 2.")
        elif isinstance(le, int):
            if le < 0 or le > 65536:
                raise ValueError("`le` must be in range 0 ~ 65536")
            if le == 0:
                le = ""
            elif le <= 256:
                le = bytes([le & 0xff])
            else:
                le = struct.pack(">H", le)
        else:
            raise TypeError("Type of `le` must be `str` or `int`.")
        if len(le) == 2 and len(self.lc) == 1:
            self.__fields[4] = b"\x00\x00" + self.__fields[4]
            self.__fields[6] = le
        elif len(le) == 1 and len(self.lc) == 3:
            self.__fields[6] = b"\x00" + le
        else:
            self.__fields[6] = le

    def is_extended(self):
        """
        Is this APDU extended APDU.
        """
        return len(self.lc) > 1 or len(self.le) > 1


class RspAPDU:
    """
    Response APDU.
    """

    def __init__(self, val=b"\x90\x00", time=0.0):
        if isinstance(val, str):
            val = bytes.fromhex(val)
        if not isinstance(val, bytes):
            val = bytes(val)

        if len(val) < 2:
            raise ValueError("Length of `val` must be larger 2")

        self.__val = val
        self.__time = time

    @property
    def data(self):
        """
        Getter for data field of response APDU.
        """
        return self.__val[:-2]

    @property
    def sw(self):
        """
        Getter for status word of response APDU.
        """
        return self.__val[-2:]

    @property
    def sw1(self):
        """
        Getter for the first byte of status word of response APDU.
        """
        return self.__val[-2:-1]

    @property
    def sw2(self):
        """
        Getter for the second byte of status word of response APDU.
        """
        return self.__val[-1:]

    @property
    def time(self):
        """
        Getter for time elapsed of response APDU.
        """
        return self.__time

    def __bytes__(self):
        return self.__val

    def __str__(self):
        return self.__val.hex()

    def __repr__(self):
        return f"RspAPDU('{self}')"


class AID:
    def __init__(self, val):
        if isinstance(val, str):
            val = bytes.fromhex(val)
        elif isinstance(val, AID):
            val = bytes(val)
        elif not isinstance(val, bytes):
            raise TypeError(val)

        if len(val) < 5 or len(val) > 16:
            raise ValueError(val)

        self.__val = val

    def __bytes__(self):
        return self.__val

    def __repr__(self):
        return f"AID('{self.__val.hex()}')"

    @property
    def rid(self):
        return self.__val[:5]

    def __eq__(self, other):
        try:
            if isinstance(other, str):
                return self.__val == bytes.fromhex(other)
            elif isinstance(other, bytes):
                return self.__val == other
            elif isinstance(other, AID):
                return self.__val == bytes(other)
            return False
        except Exception:
            return False


def lv_bytes(data):
    if isinstance(data, str):
        data = bytes.fromhex(data)
    elif not isinstance(data, bytes):
        data = bytes(data)

    datas = []
    data_len = len(data)
    if data_len < 128:
        datas.append(struct.pack('>B', data_len))
    elif data_len < 256:
        datas.append(b'\x81')
        datas.append(struct.pack('>B', data_len))
    elif data_len < 65536:
        datas.append(b'\x82')
        datas.append(struct.pack('>H', data_len))
    else:
        raise ValueError('data length not supported')

    datas.append(data)
    return b''.join(datas)


def tlv_bytes(tag, data):
    if isinstance(tag, bytes):
        pass
    elif isinstance(tag, str):
        tag = bytes.fromhex(tag)
    elif isinstance(tag, int):
        if tag < 256:
            tag = struct.pack(">B", tag)
        elif tag < 65536:
            tag = struct.pack(">H", tag)
        else:
            raise ValueError(tag)
    else:
        tag = bytes(tag)

    return tag + lv_bytes(data)


class RspError(Exception):
    pass


__all__ = [
    'CmdAPDU',
    'RspAPDU',
    'AID',
    'RspError',
    'lv_bytes',
    'tlv_bytes',
]
