#!/usr/bin/env python
# coding=utf-8
import struct
import six
import json

def DecodeAnyAttr(val):
    if val is None:
        return ''
    else:
        if isinstance(val, unicode):
            try:
                return val.encode('utf-8')
            except:
                return val.encode('gb2312')

        else:
            if isinstance(val, str):
                return val
            if isinstance(val, int):
                return str(val)
            if isinstance(val, float):
                return str(val)
            if isinstance(val, (dict, list)):
                return json.dumps(val, ensure_ascii=False)
            try:
                return str(val)
            except:
                return val

        return


def EncodeString(str):
    if len(str) > 253:
        raise ValueError('Can only encode strings of <= 253 characters')
    if isinstance(str, six.text_type):
        return str.encode('utf-8')
    else:
        return str


def EncodeOctets(str):
    if len(str) > 253:
        raise ValueError('Can only encode strings of <= 253 characters')
    return str


def EncodeAddress(addr):
    if not isinstance(addr, six.string_types):
        raise TypeError('Address has to be a string')
    a, b, c, d = map(int, addr.split('.'))
    return struct.pack('BBBB', a, b, c, d)


def EncodeInteger(num):
    if not isinstance(num, six.integer_types):
        raise TypeError('Can not encode non-integer({0}) as integer'.format(num))
    return struct.pack('!I', num)


def EncodeDate(num):
    if not isinstance(num, int):
        raise TypeError('Can not encode non-integer as date')
    return struct.pack('!I', num)


def DecodeString(str):
    try:
        return str.decode('utf-8')
    except:
        return str


def DecodeOctets(str):
    return str


def DecodeAddress(addr):
    return '.'.join(map(str, struct.unpack('BBBB', addr)))


def DecodeInteger(num):
    return struct.unpack('!I', num)[0]


def DecodeDate(num):
    return struct.unpack('!I', num)[0]


def EncodeAttr(datatype, value):
    if datatype == 'string':
        return EncodeString(value)
    if datatype == 'octets':
        return EncodeOctets(value)
    if datatype == 'ipaddr':
        return EncodeAddress(value)
    if datatype == 'integer':
        return EncodeInteger(value)
    if datatype == 'date':
        return EncodeDate(value)
    raise ValueError('Unknown attribute type %s' % datatype)


def DecodeAttr(datatype, value):
    if datatype == 'string':
        return DecodeString(value)
    if datatype == 'octets':
        return DecodeOctets(value)
    if datatype == 'ipaddr':
        return DecodeAddress(value)
    if datatype == 'integer':
        return DecodeInteger(value)
    if datatype == 'date':
        return DecodeDate(value)
    raise ValueError('Unknown attribute type %s' % datatype)