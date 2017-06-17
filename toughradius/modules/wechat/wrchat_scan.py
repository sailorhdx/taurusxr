#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer
from toughradius.toughlib.dbutils import make_db
from toughradius.modules import models
from toughradius.common import wxrouter

class WechatEventDispatch:
    """ 微信扫码事件 """

    @defer.inlineCallbacks
    def wxrouter_event_scan(self, msg, gdata = None, wechat = None, **kwargs):
        yield
        if msg.key.startswith('oprbind_qr_'):
            builder_id = msg.key[11:]
            resp = yield wxrouter.dispatch(msg, gdata=gdata, wechat=wechat, func='oprbind_qr_scan', builder_id=msg.key[11:], **kwargs)
        else:
            resp = wechat.response_none()
        defer.returnValue(resp)

    @defer.inlineCallbacks
    def wxrouter_oprbind_qr_scan(self, msg, gdata = None, wechat = None, builder_id = None, **kwargs):
        yield
        with make_db(gdata.db) as db:
            builder = db.query(models.TrBuilder).get(builder_id)
            if not builder:
                defer.returnValue(wechat.response_text(u'无效的绑定码'))
            if builder.wechat_oid:
                defer.returnValue(wechat.response_text(u'微信账号已经绑定'))
            else:
                builder.wechat_oid = msg.source
                db.commit()
                defer.returnValue(wechat.response_text(u'微信账号绑定成功'))


router = WechatEventDispatch()