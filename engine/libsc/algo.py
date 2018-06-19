#coding:utf-8
"""
Privide some algorithoms.
"""

import pyDes
import cryptolib as cl

PAD_NONE = 0
PAD_9797M2 = 1

DEFAULT_IV = b"\x00" * 8


def _add_padding(data, pad):
    if pad == PAD_NONE:
        return data
    elif pad == PAD_9797M2:
        pad_len = 8 - len(data) % 8
        datas = [data, b'\x80', b'\x00' * (pad_len - 1)]
        return b''.join(datas)
    else:
        raise ValueError(f"pad type {pad} not supported.")


def _rm_padding(data, pad):
    if pad == PAD_NONE:
        return data
    elif pad == PAD_9797M2:
        for i in range(-1, -len(data) - 1, -1):
            if data[i] == 0x00:
                continue
            elif data[i] == 0x80:
                return data[:i]
            else:
                raise ValueError("padding of data is not PAD_9797M2")

    else:
        raise ValueError(f"pad type {pad} not supported.")


def tdes_cbc_enc(key, data, iv=DEFAULT_IV, pad=PAD_NONE) -> bytes:
    data = _add_padding(data, pad)
    tdes = pyDes.triple_des(key, mode=pyDes.CBC, IV=iv)
    return tdes.encrypt(data)


def tdes_cbc_dec(key, data, iv=DEFAULT_IV, pad=PAD_NONE) -> bytes:
    tdes = pyDes.triple_des(key, mode=pyDes.CBC, IV=iv)
    ret = tdes.decrypt(data)
    return _rm_padding(ret, pad)


def tdes_ecb_enc(key, data, pad=PAD_NONE) -> bytes:
    data = _add_padding(data, pad)
    tdes = pyDes.triple_des(key, mode=pyDes.ECB)
    return tdes.encrypt(data)


def tdes_ecb_dec(key, data, pad=PAD_NONE) -> bytes:
    tdes = pyDes.triple_des(key, mode=pyDes.ECB)
    ret = tdes.decrypt(data)
    return _rm_padding(ret, pad)


def tdes_mac(key, data, iv=DEFAULT_IV, pad=PAD_NONE) -> bytes:
    return tdes_cbc_enc(key, data, iv, pad)[-8:]


def tdes_mac_9797m2_alg3(key, data, iv=DEFAULT_IV) -> bytes:
    data = _add_padding(data, PAD_9797M2)
    if len(data) > 8:
        iv = des_mac(key[:8], data[:-8], iv, PAD_NONE)
    mac = tdes_mac(key, data[-8:], iv, PAD_NONE)
    return mac


def des_cbc_enc(key, data, iv=DEFAULT_IV, pad=PAD_NONE) -> bytes:
    data = _add_padding(data, pad)
    tdes = pyDes.des(key, mode=pyDes.CBC, IV=iv)
    return tdes.encrypt(data)


def des_cbc_dec(key, data, iv=DEFAULT_IV, pad=PAD_NONE) -> bytes:
    tdes = pyDes.des(key, mode=pyDes.CBC, IV=iv)
    ret = tdes.decrypt(data)
    return _rm_padding(ret, pad)


def des_ecb_enc(key, data, pad=PAD_NONE) -> bytes:
    data = _add_padding(data, pad)
    tdes = pyDes.des(key, mode=pyDes.ECB)
    return tdes.encrypt(data)


def des_ecb_dec(key, data, pad=PAD_NONE) -> bytes:
    tdes = pyDes.des(key, mode=pyDes.ECB)
    ret = tdes.decrypt(data)
    return _rm_padding(ret, pad)


def des_mac(key, data, iv=DEFAULT_IV, pad=PAD_NONE) -> bytes:
    return des_cbc_enc(key, data, iv, pad)[-8:]


__all__ = [
    "tdes_cbc_enc",
    "tdes_cbc_dec",
    "tdes_ecb_enc",
    "tdes_ecb_dec",
    "des_cbc_enc",
    "des_cbc_dec",
    "des_ecb_enc",
    "des_ecb_dec",
    "tdes_mac",
    "tdes_mac_9797m2_alg3",
    "des_mac",
    "PAD_NONE",
    "PAD_9797M2",
]