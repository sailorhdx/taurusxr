#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer

class WechatEventDispatch:
    """ 微信菜单链接视图事件"""

    @defer.inlineCallbacks
    def wxrouter_event_view(self, msg, gdata = None, **kwargs):
        yield
        defer.returnValue('')


router = WechatEventDispatch()