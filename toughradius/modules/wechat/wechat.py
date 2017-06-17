#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer
from toughradius.toughlib import logger, utils
from toughradius.common import wxrouter
from toughradius.modules.wechat import wechat_funcs

class WechatMsgTypeDispatch:

    @defer.inlineCallbacks
    def wxrouter_text(self, msg, gdata = None, wechat = None, **kwargs):
        logger.info(u'process wechat text %s' % utils.safeunicode(msg.content))
        resp = ''
        keychar = msg.content.strip()
        if keychar in wechat_funcs:
            logger.info('execute func %s' % wechat_funcs[keychar])
            resp = yield wxrouter.dispatch(msg, gdata=gdata, wechat=wechat, func=wechat_funcs[keychar], **kwargs)
        defer.returnValue(resp)

    @defer.inlineCallbacks
    def wxrouter_link(self, msg, gdata = None, **kwargs):
        yield
        defer.returnValue('')

    @defer.inlineCallbacks
    def wxrouter_video(self, msg, gdata = None, **kwargs):
        yield
        defer.returnValue('')

    @defer.inlineCallbacks
    def wxrouter_location(self, msg, gdata = None, **kwargs):
        yield
        defer.returnValue('')

    @defer.inlineCallbacks
    def wxrouter_voice(self, msg, gdata = None, **kwargs):
        yield
        defer.returnValue('')

    @defer.inlineCallbacks
    def wxrouter_shortvideo(self, msg, gdata = None, **kwargs):
        yield
        defer.returnValue('')


router = WechatMsgTypeDispatch()