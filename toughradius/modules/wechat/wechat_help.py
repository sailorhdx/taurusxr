#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer
from toughradius.modules import models
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib import logger
from toughradius.toughlib import utils

class WechatEventDispatch:

    @defer.inlineCallbacks
    def wxrouter_mps_help(self, msg, gdata = None, wechat = None, **kwargs):
        """ 帮助信息 """
        yield
        defer.returnValue(wechat.response_text(''))


router = WechatEventDispatch()