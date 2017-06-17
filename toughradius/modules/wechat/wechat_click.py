#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import logger
from twisted.internet import defer
from toughradius.common import wxrouter

class WechatEventDispatch:
    """ 微信菜单点击事件，菜单事件名称在管理菜单中定义"""

    @defer.inlineCallbacks
    def wxrouter_event_click(self, msg, gdata = None, wechat = None, **kwargs):
        resp = yield wxrouter.dispatch(msg, gdata=gdata, wechat=wechat, func=('menu_%s' % msg.key), **kwargs)
        defer.returnValue(resp)


router = WechatEventDispatch()