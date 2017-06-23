#!/usr/bin/env python
# coding=utf-8
import struct

def bytes2hex(bytes):
    num = len(bytes)
    hexstr = u''
    for i in range(num):
        t = u'%x' % bytes[i]
        if len(t) % 2:
            hexstr += u'0'
        hexstr += t

    return hexstr.upper()


def isimg(filename):
    binfile = open(filename, 'rb')
    tpmap = {'FFD8FF': 'jpg',
     '89504E47': 'png',
     '47494638': 'gif'}
    ftype = 'unknown'
    for hcode in tpmap.keys():
        numOfBytes = len(hcode) / 2
        binfile.seek(0)
        hbytes = struct.unpack_from('B' * numOfBytes, binfile.read(numOfBytes))
        f_hcode = bytes2hex(hbytes)
        if f_hcode == hcode:
            ftype = tpmap[hcode]
            break

    binfile.close()
    return ftype in ('jpg', 'png', 'gif')


if __name__ == '__main__':
    print isimg('D:/portrait.jpg')