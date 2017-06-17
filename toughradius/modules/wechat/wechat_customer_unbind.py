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
    def wxrouter_customer_unbind(self, msg, gdata = None, wechat = None, **kwargs):
        """ 客户取消绑定 """
        yield
        with make_db(gdata.db) as db:
            try:
                customer = db.query(models.TrCustomer).filter(models.TrCustomer.wechat_oid == msg.source).first()
                if customer:
                    customer.wechat_oid = ''
                    db.commit()
                    rtext = u'用户微信解绑成功，若要再次绑定请通过菜单-账号绑定操作。'
                    defer.returnValue(wechat.response_text(rtext))
                else:
                    defer.returnValue(wechat.response_text(u'用户未绑定'))
            except Exception as err:
                db.rollback()
                logger.exception(err, trace='wechat')
                defer.returnValue(wechat.response_text(u'服务器错误,请联系客服 %s' % utils.safeunicode(err)))


router = WechatEventDispatch()