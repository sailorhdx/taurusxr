#!/usr/bin/env python
# coding=utf-8
from toughradius.modules import models
from toughradius.toughlib import utils, logger
from toughradius.toughlib.storage import Storage
from toughradius.common import tools
import functools
import json

def logparams(func):

    @functools.wraps(func)
    def warp(*args, **kargs):
        logger.info('%s %s' % (repr(args), repr(kargs)))
        return func(*args, **kargs)

    return warp


supopr = Storage()
supopr.operator_name = 'admin'
supopr.operate_ip = '0.0.0.0'
supopr.username = 'admin'
supopr.ipaddr = '0.0.0.0'

class BaseService(object):

    def __init__(self, db, aes, debug = False, operator = None, config = None):
        self.db = db
        self.aes = aes
        self.last_error = ''
        self.debug = debug
        self.operator = operator or supopr
        self.config = config

    def parse_arg(self, formdata, name, defval = None, rule = None):
        value = formdata.get(name, defval)
        value = formdata.get(name)
        value = value if value is not None else defval
        if rule is None:
            return value
        else:
            if hasattr(rule, 'valid') and not rule.valid(value):
                raise ValueError(u'param {0}:{1}'.format(name, rule.msg))
            return value

    def update_account_attr(self, account_number, name, value, attr_type = 0):
        attr = self.db.query(models.TrAccountAttr).filter_by(attr_name=name).first()
        if not attr:
            attr = models.TrAccountAttr()
            attr.id = utils.get_uuid()
            attr.account_number = account_number
            attr.attr_type = attr_type
            attr.attr_name = name
            attr.attr_value = value
            attr.attr_desc = name
            attr.sync_ver = tools.gen_sync_ver()
            self.db.add(attr)
        else:
            attr.attr_value = value

    def add_oplog(self, message):
        ops_log = models.TrOperateLog()
        ops_log.id = utils.get_uuid()
        ops_log.operator_name = self.operator.username
        ops_log.operate_ip = self.operator.ipaddr
        ops_log.operate_time = utils.get_currtime()
        ops_log.operate_desc = message
        self.db.add(ops_log)