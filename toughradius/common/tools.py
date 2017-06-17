#!/usr/bin/env python
# coding=utf-8
import os
import uuid
import time
import random, string
from hashlib import md5
from decimal import Decimal
import sys
from twisted.internet import utils as txutils
import shutil

def get_sys_uuid():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    return md5(':'.join([ mac[e:e + 2] for e in range(0, 11, 2) ])).hexdigest()


def get_sys_token():
    return txutils.getProcessOutput('/usr/local/bin/toughkey')


def gen_num_id(c = 16):
    return int(str(Decimal(time.time())).replace('.', '')[:c])


def gen_sync_ver():
    return int(str(Decimal(time.time())).replace('.', '')[:16])


def copydir(src, dst, excludes = []):
    try:
        names = os.walk(src)
        for root, dirs, files in names:
            for i in files:
                srcname = os.path.join(root, i)
                dir = root.replace(src, '')
                dirname = dst + dir
                if os.path.exists(dirname):
                    pass
                else:
                    os.makedirs(dirname)
                dirfname = os.path.join(dirname, i)
                if dirfname not in excludes:
                    shutil.copy2(srcname, dirfname)

    except Exception as e:
        import traceback
        traceback.print_exc()

def gen_random_str(randomlength=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str

def gen_random_num(randomlength=8):
    str = ''
    chars = '0123456789'
    length = len(chars) - 1
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str

def get_aliyun_license():
    print 'this is empty method(get_aliyun_license)'
def get_free_license():
    print 'this is empty method(get_free_license)'
def upgrade_release(savepath):
    print 'this is empty method(upgrade_release)'

if __name__ == '__main__':
    print get_sys_uuid()
    print gen_random_str(20)
    print gen_random_num(20)
    upgrade_release('fdfd')