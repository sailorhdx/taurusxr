#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils, logger, dispatch
from twisted.internet import reactor
from toughradius.modules import models
from toughradius.modules.events.event_basic import BasicEvent

class SendWechatEvent(BasicEvent):

    def event_send_wechat(self, wechat_oid, content = None):
        if wechat_oid and self.wechat and content:
            reactor.callLater(0.5, self.wechat.send_text_message, wechat_oid, content)


def __call__(dbengine = None, mcache = None, wechat = None, **kwargs):
    return SendWechatEvent(dbengine=dbengine, mcache=mcache, wechat=wechat, **kwargs)