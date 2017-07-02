#!/usr/bin/env python
#coding:utf-8
import hmac
import re

import time
from Crypto.Cipher import AES
from Crypto import Random
import hashlib
import base64
import os
import json

import sqlalchemy
from sqlalchemy import create_engine
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired

from taurusxradius.common import tools, safefile
from taurusxradius.modules import models
from taurusxradius.taurusxlib import utils
from sqlalchemy.sql import text as _sql


import math
import decimal

from taurusxradius.taurusxlib.mail import send_mail


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


class QXToken(object):
    def __init__(self, name, key):
        self.name = name
        self.key = key

    def generate_auth_token(self, expiration=3600):
        s = Serializer(self.key, expires_in=expiration)
        return s.dumps({'name': self.name})

    def verify_auth_token(self, token):
        s = Serializer(self.key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        return data['name'] == self.name


if __name__ == '__main__':
    import sys
    if sys.maxunicode > 65535:
        print 'UCS4 build'
    else:
        print 'UCS2 build'
    """
    db_engine = create_engine("mysql://root:Root123@115.47.117.189:3306/taurusxr", max_overflow=5)
    with db_engine.begin() as conn:
        sql = '\n                select bas.ip_addr  \n                from tr_bas as bas,tr_customer as cus,tr_account as user,tr_bas_node as bn\n                where cus.customer_id = user.customer_id\n                    and cus.node_id = bn.node_id\n                    and bn.bas_id = bas.id\n                    and user.account_number = :account_number\n                '
        cur = conn.execute(_sql(sql), account_number='test')
        for i in cur.fetchall():
            # 打印结果
            print(i)
            print(i[0] + ',' + i.ip_addr)
       # print cur.fetchall()
        #ipaddrs = [ addr.ip_addr for addr in cur]
        #print ipaddrs
    m = re.match('(\w\w\w)-(\d\d\d)', 'abc-123')
    if m is not None:
        print '1111'
        print m.group()
        print m.groups()
    else:
        print '2222'
    """
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

    key = "JD98Dskw=23njQndW9D"
    # 生成用户token

    token = QXToken('zl',key)
    strToken  = token.generate_auth_token()
    print token.generate_auth_token()

    uuid = 'h@neusoft.com'


    # 验证token
    token = QXToken('zl',key)
    print token.verify_auth_token(strToken)