#coding:utf-8

from abc import ABC, abstractmethod
import struct
import logging
log = logging.getLogger("libsc")

from .base import *
from .reader import Reader
from .algo import *
from .javacard import *

C_MAC = 1
C_ENCRYPT_MAC = 3


class SecureChannelError(Exception):
    pass


class SecureChannel(ABC):
    @abstractmethod
    def init_secure_channel(self, reader):
        pass

    @abstractmethod
    def external_auth(self, prev_apdu, prev_rsp):
        pass

    @abstractmethod
    def is_secure(self):
        pass

    @abstractmethod
    def get_secure_level(self):
        pass

    @abstractmethod
    def wrap(self, apdu):
        pass

    @abstractmethod
    def unwrap(self, rsp):
        pass

    @abstractmethod
    def encrypt_data(self, data):
        pass

    @abstractmethod
    def decrypt_data(self, data):
        pass


class SCP02I55(SecureChannel):
    def __init__(self, secure_level=0, keysets=None):
        if secure_level not in [0, C_MAC, C_ENCRYPT_MAC]:
            raise ValueError(secure_level)
        if keysets is None:
            keysets = {
                0xff: (
                    # key ENC
                    bytes.fromhex("404142434445464748494A4B4C4D4E4F"),
                    # key MAC
                    bytes.fromhex("404142434445464748494A4B4C4D4E4F"),
                    # key DEK
                    bytes.fromhex("404142434445464748494A4B4C4D4E4F"),
                )
            }
        self.__keysets = keysets
        self.__secure_level = secure_level
        self.__reset()

    def __reset(self):
        self.__session_keys = None
        self.__apdu_mac = None
        self.__is_secure = False

    def __gen_session_key(self, constant, seq_counter, static_key):
        key_derivation = constant + seq_counter + b"\x00" * 12
        return tdes_cbc_enc(static_key, key_derivation)

    def __gen_session_keys(self, seq_counter, key_version):
        keyset = self.__keysets.get(key_version)
        if keyset is None:
            raise SecureChannelError(
                f"key version {key_version:02x} is not defined!")

        self.__session_keys = []
        self.__session_keys.append(
            self.__gen_session_key(b"\x01\x82", seq_counter, keyset[0]))
        self.__session_keys.append(
            self.__gen_session_key(b"\x01\x01", seq_counter, keyset[1]))
        self.__session_keys.append(
            self.__gen_session_key(b"\x01\x81", seq_counter, keyset[2]))

        log.debug(f"session key (ENC): {self.__session_keys[0].hex()}")
        log.debug(f"session key (MAC): {self.__session_keys[1].hex()}")
        log.debug(f"session key (DEK): {self.__session_keys[2].hex()}")

    def __gen_card_cryptogram(self, seq_counter, card_challenge,
                              host_challenge):
        datas = []
        datas.append(host_challenge)
        datas.append(seq_counter)
        datas.append(card_challenge)
        cryptogram = tdes_mac(
            self.__session_keys[0], b''.join(datas), pad=PAD_9797M2)
        log.debug(f"card cryptogram: {cryptogram.hex()}")
        return cryptogram

    def __gen_host_cryptogram(self, seq_counter, card_challenge,
                              host_challenge):
        datas = []
        datas.append(seq_counter)
        datas.append(card_challenge)
        datas.append(host_challenge)
        cryptogram = tdes_mac(
            self.__session_keys[0], b''.join(datas), pad=PAD_9797M2)
        log.debug(f"host cryptogram: {cryptogram.hex()}")
        return cryptogram

    def __add_apdu_mac(self, apdu: CmdAPDU, is_auth=False):
        assert isinstance(apdu, CmdAPDU)

        if is_auth:
            temp_icv = b'\x00' * 8
        else:
            temp_icv = des_ecb_enc(self.__session_keys[1][:8], self.__apdu_mac)

        if len(apdu.data) + 8 > 255:
            raise ValueError(
                f"data field of apdu is too long to add MAC: {apdu}")

        new_apdu = CmdAPDU(apdu)
        new_apdu.cla = apdu.cla[0] | 0x04 # add secure message bit
        new_apdu.data += b"\x00" * 8 # this makes LC correct
        new_apdu.le = b""  # remove LE
        bs = bytes(new_apdu)[:-8]  # remove last 8 zeros

        log.debug(f"data to gen mac: {bs.hex()}")
        mac = tdes_mac_9797m2_alg3(self.__session_keys[1], bs, temp_icv)

        self.__apdu_mac = mac
        new_apdu.data = new_apdu.data[:-8] + mac
        return new_apdu

    def __encrypt_apdu(self, apdu: CmdAPDU):
        assert isinstance(apdu, CmdAPDU)
        pass

    def init_secure_channel(self, reader: Reader):
        apdu = CmdAPDU("80500000081122334455667788")
        rsp = reader.transmit(apdu)
        self.external_auth(reader, apdu, rsp)

    def external_auth(self, reader: Reader, prev_apdu: CmdAPDU,
                      prev_rsp: RspAPDU):
        if prev_apdu.ins != b"\x80" and len(prev_apdu.data) != 8:
            raise SecureChannelError("Command APDU of Init-Update error.")
        if prev_rsp.sw != b'\x90\x00' or len(prev_rsp.data) != 28:
            raise SecureChannelError("Response of Init-Update error.")

        self.__reset()
        data = prev_rsp.data

        key_diver_data = data[:10]
        key_version = data[10]
        scp_version = data[11]
        if scp_version != 2:
            raise SecureChannelError("SCP02 not supported in card!")
        seq_counter = data[12:14]
        card_challenge = data[14:20]
        card_cryptogram1 = data[20:28]
        host_challenge = prev_apdu.data

        log.debug(f"keyset version is {key_version:02x}")
        log.debug(f"sequence counter is {seq_counter.hex()}")
        log.debug(f"card challenge is {card_challenge.hex()}")
        log.debug(f"host challenge is {host_challenge.hex()}")
        log.debug(f"card cryptogram received: {card_cryptogram1.hex()}")

        self.__gen_session_keys(seq_counter, key_version)
        card_cryptogram = self.__gen_card_cryptogram(
            seq_counter, card_challenge, host_challenge)
        if card_cryptogram != card_cryptogram1:
            raise SecureChannelError("Card cryptogram error.")

        host_cryptogram = self.__gen_host_cryptogram(
            seq_counter, card_challenge, host_challenge)

        apdu = CmdAPDU("84820000")
        apdu.p1 = self.__secure_level
        apdu.data = host_cryptogram

        apdu = self.__add_apdu_mac(apdu, True)

        rsp = reader.transmit(apdu)
        if rsp.sw != b"\x90\x00":
            raise SecureChannelError("External Authenticate failed.")

        self.__is_secure = True

    def is_secure(self):
        return self.__is_secure

    def get_secure_level(self):
        return self.__secure_level

    def wrap(self, apdu):
        if not self.is_secure():
            raise SecureChannelError("Secure channel is not established.")
        if self.get_secure_level() == 0:
            return apdu
        elif self.get_secure_level() == C_MAC:
            return self.__add_apdu_mac(apdu)
        else:
            assert self.get_secure_level() == C_ENCRYPT_MAC
            # TODO: implement me
            pass

    def unwrap(self, rsp):
        if not self.is_secure():
            raise SecureChannelError("Secure channel is not established.")
        # do not need to do anything for SCP02 i=55
        return rsp

    def encrypt_data(self, data):
        if not self.is_secure():
            raise SecureChannelError("Secure channel is not established.")

        return tdes_ecb_enc(self.__session_keys[2], data)

    def decrypt_data(self, data):
        if not self.is_secure():
            raise SecureChannelError("Secure channel is not established.")

        return tdes_ecb_dec(self.__session_keys[2], data)


class SecurityDomain:
    def __init__(self, reader: Reader, sd_aid=b""):
        if not isinstance(reader, Reader):
            raise TypeError(reader)
        self.__reader = reader
        self.__sd_aid = sd_aid
        self.__sc = None

    def select(self, aid=b""):
        if isinstance(aid, str):
            aid = bytes.fromhex(aid)
        elif isinstance(aid, AID):
            aid = bytes(aid)
        elif not isinstance(aid, bytes):
            raise TypeError(aid)

        cmd = CmdAPDU("00A4040000")
        cmd.data = aid

        rsp = self.__reader.transmit(cmd)
        return rsp

    def reset(self, reset_reader=True):
        self.__sc = None
        if reset_reader:
            self.__reader.reset()

    def prepare(self, secure_level=C_MAC):
        self.__sc = SCP02I55(secure_level)
        rsp = self.select(self.__sd_aid)
        if rsp.sw != b'\x90\x00':
            raise RspError(f"select {bytes(self.__sd_aid).hex()} failed.")
        self.__sc.init_secure_channel(self.__reader)

    def load_cap(self, cap_file):
        if isinstance(cap_file, str):
            cap = CapFile(cap_file)
        elif isinstance(cap_file, CapFile):
            cap = cap_file
        else:
            raise TypeError(cap_file)

        if not self.__sc:
            self.prepare()

        cap_data = b''.join([
            cap.Header,
            cap.Directory,
            cap.Import,
            cap.Applet,
            cap.Class,
            cap.Method,
            cap.StaticField,
            cap.Export,
            cap.ConstantPool,
            cap.RefLocation,
        ])

        apdus = []
        # INSTALL for load APDU
        apdu = CmdAPDU("80E60200")
        apdu.data = lv_bytes(cap.pkg_aid) + bytes.fromhex("00 00 00 00")

        apdus.append(apdu)

        # load APDUs
        load_data = tlv_bytes(0xC4, cap_data)
        for i, offset in enumerate(range(0, len(load_data), 240)):
            apdu = CmdAPDU("80E80000")
            apdu.p1 = 0x00 if offset + 240 < len(load_data) else 0x80
            apdu.p2 = i & 0xff
            apdu.data = load_data[offset: offset + 240]
            apdus.append(apdu)

        # now send all APDUs
        for apdu in apdus:
            apdu = self.__sc.wrap(apdu)
            rsp = self.__reader.transmit(apdu)
            if rsp.sw != b'\x90\x00':
                raise RspError('loading CAP file failed.')

    def install_applet(self, pkg_aid, applet_aid, instance_aid=None):
        if not self.__sc:
            self.prepare()
        
        # INSTALL for install and make selectable APDU
        apdu = CmdAPDU("80E60C00")
        if instance_aid is None:
            instance_aid = applet_aid

        apdu.data = lv_bytes(pkg_aid) + lv_bytes(applet_aid) + lv_bytes(instance_aid) + bytes.fromhex('01 00 02 c900 00')

        apdu = self.__sc.wrap(apdu)
        rsp = self.__reader.transmit(apdu)
        if rsp.sw != b'\x90\x00':
            raise RspError('loading CAP file failed.')

    def remove(self, aid):
        if not self.__sc:
            self.prepare()

        apdu = CmdAPDU("80E40080")
        apdu.data = tlv_bytes(b'\x4f', aid)

        apdu = self.__sc.wrap(apdu)
        rsp = self.__reader.transmit(apdu)
        if rsp.sw != b'\x90\x00':
            raise RspError('removing package failed.')


__all__ = [
    "SecureChannel",
    "SecureChannelError",
    "SCP02I55",
    "SecurityDomain",
]
