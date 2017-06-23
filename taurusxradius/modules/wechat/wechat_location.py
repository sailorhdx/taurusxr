#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer

class WechatEventDispatch:
    """ 位置上报事件 """

    @defer.inlineCallbacks
    def wxrouter_event_location(self, msg, gdata = None, **kwargs):
        yield
        defer.returnValue('')


router = WechatEventDispatch()