#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer
from twisted.internet import defer
from taurusxradius.modules import models
from taurusxradius.taurusxlib.storage import Storage
from taurusxradius.taurusxlib.dbutils import make_db
from taurusxradius.taurusxlib import logger
from taurusxradius.taurusxlib import utils

class WechatEventDispatch:
    """ 用户退订事件 """

    @defer.inlineCallbacks
    def wxrouter_event_unsubscribe(self, msg, gdata = None, wechat = None, **kwargs):
        yield
        defer.returnValue(wechat.response_none())


router = WechatEventDispatch()