#!/usr/bin/env python
#coding:utf-8
import re

from Crypto.Cipher import AES
from Crypto import Random
import hashlib
import base64
import os
import json

from toughradius.common import tools, safefile
from toughradius.toughlib import utils

import math
import decimal

class AESCipher:

    def __init__(self,key=None):
        if key:self.setup(key)

    def is_pwd_encrypt(self):
        return os.environ.get("CLOSE_PASSWORD_ENCRYPTION")

    def setup(self, key):
        self.bs = 32
        self.ori_key = key
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        is_encrypt = self.is_pwd_encrypt()
        if is_encrypt:
            return raw

        raw = safestr(raw)
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        is_encrypt = self.is_pwd_encrypt()
        if is_encrypt:
            return enc

        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return safeunicode(self._unpad(cipher.decrypt(enc[AES.block_size:])))

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def _unpad(self,s):
        return s[:-ord(s[len(s)-1:])]

def safestr(val):
    if val is None:
        return ''

    if isinstance(val, unicode):
        try:
            return val.encode('utf-8')
        except:
            return val.encode('gb2312')
    elif isinstance(val, str):
        return val
    elif isinstance(val, int):
        return str(val)
    elif isinstance(val, float):
        return str(val)
    elif isinstance(val, (dict,list)):
        return json.dumps(val, ensure_ascii=False)
    else:
        try:
            return str(val)
        except:
            return val
    return val

def safeunicode(val):
    if val is None:
        return u''

    if isinstance(val, str):
        try:
            return val.decode('utf-8')
        except:
            try:
                return val.decode('gb2312')
            except:
                return val
    elif isinstance(val, unicode):
        return val
    elif isinstance(val, int):
        return str(val).decode('utf-8')
    elif isinstance(val, float):
        return str(val).decode('utf-8')
    elif isinstance(val, (dict,list)):
        return json.dumps(val)
    else:
        try:
            return str(val).decode('utf-8')
        except:
            return val
    return val

def changeTime(allTime):
    day = 24 * 60 * 60
    hour = 60 * 60
    min = 60
    if allTime < 60:
        return "%d sec" % math.ceil(allTime)
    elif allTime > day:
        days = divmod(allTime, day)
        return "%d days, %s" % (int(days[0]), changeTime(days[1]))
    elif allTime > hour:
        hours = divmod(allTime, hour)
        return '%d hours, %s' % (int(hours[0]), changeTime(hours[1]))
    else:
        mins = divmod(allTime, min)
        return "%d mins, %d sec" % (int(mins[0]), math.ceil(mins[1]))

if __name__ == '__main__':
    m = re.match('(\w\w\w)-(\d\d\d)', 'abc-123')
    if m is not None:
        print '1111'
        print m.group()
        print m.groups()
    else:
        print '2222'

    aes = AESCipher("0pNxtSi4kFaK2MEZTLYIATnQIdrCPtLq")
    aa = aes.encrypt(u"中文".encode('utf-8'))
    print aa
    cc = aes.decrypt(aa)
    print cc.encode('utf-8')


    aa = aes.decrypt("L8EARF/vJsEZx6zkmyQeLnfukUqZXYVq701lAALGTL7ehFyWJ9F632kMwECtpR48")
    print aa
    bb = """
\xe5\x88\xa0\xe9\x99\xa4\xe7\xb3\xbb\xe7\xbb\x9f\xe6\x97\xa5\xe5\xbf\x97
        
        :param name: \xe6\x97\xa5\xe5\xbf\x97\xe5\x90\x8d\xe7\xa7\xb0 (info,debug,error,exception,event,api)
        :type name: string        
    """
    print bb










