#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer
from twisted.internet import defer
from toughradius.modules import models
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib import logger
from toughradius.toughlib import utils

class WechatEventDispatch:
    """ 用户退订事件 """

    @defer.inlineCallbacks
    def wxrouter_event_unsubscribe(self, msg, gdata = None, wechat = None, **kwargs):
        yield
        defer.returnValue(wechat.response_none())


router = WechatEventDispatch()