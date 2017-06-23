#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer
from taurusxradius.modules import models
from taurusxradius.taurusxlib.storage import Storage
from taurusxradius.taurusxlib.dbutils import make_db
from taurusxradius.taurusxlib import logger
from taurusxradius.taurusxlib import utils

class WechatEventDispatch:

    @defer.inlineCallbacks
    def wxrouter_mps_help(self, msg, gdata = None, wechat = None, **kwargs):
        """ 帮助信息 """
        yield
        defer.returnValue(wechat.response_text(''))


router = WechatEventDispatch()