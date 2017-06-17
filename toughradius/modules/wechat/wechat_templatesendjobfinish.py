#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer

class WechatEventDispatch:
    """ 模板消息事件 """

    @defer.inlineCallbacks
    def wxrouter_event_templatesendjobfinish(self, msg, gdata = None, **kwargs):
        yield
        defer.returnValue('')


router = WechatEventDispatch()