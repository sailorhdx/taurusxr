#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer
from twisted.internet import defer
from toughradius.modules import models
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib import logger
from toughradius.toughlib import utils, dispatch
from toughradius.common import tools
from toughradius.common import wxrouter

class WechatEventDispatch:
    """ 用户订阅事件 """

    @defer.inlineCallbacks
    def wxrouter_event_subscribe(self, msg, gdata = None, wechat = None, **kwargs):
        yield
        with make_db(gdata.db) as db:
            try:
                welcome_text = db.query(models.TrParam.param_value).filter(models.TrParam.param_name == 'mps_welcome_text').scalar() or ''
                defer.returnValue(wechat.response_text(utils.safeunicode(welcome_text)))
            except Exception as err:
                logger.exception(err, trace='wechat')


router = WechatEventDispatch()