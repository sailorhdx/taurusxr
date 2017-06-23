#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer
from twisted.internet import defer
from taurusxradius.modules import models
from taurusxradius.taurusxlib.storage import Storage
from taurusxradius.taurusxlib.dbutils import make_db
from taurusxradius.taurusxlib import logger
from taurusxradius.taurusxlib import utils, dispatch
from taurusxradius.common import tools
from taurusxradius.common import wxrouter

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