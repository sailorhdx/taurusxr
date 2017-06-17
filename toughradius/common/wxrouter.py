#!/usr/bin/env python
# coding=utf-8
import os
import types
import importlib
from twisted.internet.threads import deferToThread
from twisted.python import reflect
from twisted.internet import defer
from twisted.python import log
from toughradius.toughlib import logger
from wechat_sdk import messages

class EventDispatcher:
    """
    微信事件分发器，每个微信事件只能对应到唯一函数，
    每次函数调用总是返回微信事件响应。
    函数必须全部采用twisted异步模式调用，函数加装饰器 @defer.inlineCallbacks
    """

    def __init__(self, prefix = 'wxrouter_'):
        self.prefix = prefix
        self.callbacks = {}

    def sub(self, name, func):
        self.callbacks[name] = func
        log.msg('register weixin event router %s %s' % (name, func.__doc__ or ''))

    def register(self, obj):
        d = {}
        reflect.accumulateMethods(obj, d, self.prefix)
        for k, v in d.items():
            self.sub(k, v)

    @defer.inlineCallbacks
    def _func(self, *args, **kwargs):
        logger.info('no wechat handler')
        yield
        defer.returnValue('')

    def dispatch(self, msg, gdata = None, **kwargs):
        """ 
        事件分发函数
        普通消息事件（比如主动发送文本，等）前缀为 wxrouter_消息类型
        触发消息事件（比如用户订阅，退订扫码等，）前缀为 wxrouter_event_消息类型
        参数说明：
        @msg 微信消息参数
        @gdata 系统全局变量，可以获取系统初始化后的配置
        """
        dispatch_func = kwargs.pop('func', None)
        if dispatch_func:
            return self.callbacks.get(dispatch_func, self._func)(msg, gdata=gdata, **kwargs)
        elif isinstance(msg, messages.TextMessage):
            return self.callbacks.get('text', self._func)(msg, gdata=gdata, **kwargs)
        elif isinstance(msg, messages.ImageMessage):
            return self.callbacks.get('image', self._func)(msg, gdata=gdata, **kwargs)
        elif isinstance(msg, messages.VoiceMessage):
            return self.callbacks.get('voice', self._func)(msg, gdata=gdata, **kwargs)
        elif isinstance(msg, messages.VideoMessage):
            return self.callbacks.get('video', self._func)(msg, gdata=gdata, **kwargs)
        elif isinstance(msg, messages.ShortVideoMessage):
            return self.callbacks.get('shortvideo', self._func)(msg, gdata=gdata, **kwargs)
        elif isinstance(msg, messages.LocationMessage):
            return self.callbacks.get('localtion', self._func)(msg, gdata=gdata, **kwargs)
        elif isinstance(msg, messages.LinkMessage):
            return self.callbacks.get('link', self._func)(msg, gdata=gdata, **kwargs)
        elif isinstance(msg, messages.EventMessage):
            return self.callbacks.get('event_%s' % msg.type.lower(), self._func)(msg, gdata=gdata, **kwargs)
        else:
            return


wxrouter = EventDispatcher()
sub = wxrouter.sub
dispatch = wxrouter.dispatch
register = wxrouter.register

def load_routes(route_path = None, pkg_prefix = None):
    """ 
    加载指定目录下所有的事件模块，同时注册所有模块的时间函数
    微信事件模块，必须有一个 router属性，通常为事件类的实例
    比如：
        from twisted.internet import defer
        class WechatEventDispatch:
            @defer.inlineCallbacks
            def wxrouter_event_unsubscribe(self, msg, gdata=None, **kwargs):
                defer.returnValue("")
        router = WechatEventDispatch()
    """
    evs = set((os.path.splitext(it)[0] for it in os.listdir(route_path)))
    for ev in [ it for it in evs ]:
        try:
            sub_module = os.path.join(route_path, ev)
            if os.path.isdir(sub_module):
                from toughradius.toughlib.permit import load_events
                load_events(route_path=sub_module, pkg_prefix='{0}.{1}'.format(pkg_prefix, ev))
            _ev = '{0}.{1}'.format(pkg_prefix, ev)
            robj = importlib.import_module(_ev)
            if hasattr(robj, 'router'):
                wxrouter.register(robj.router)
        except Exception as err:
            logger.error('%s, skip module %s.%s' % (str(err), pkg_prefix, ev), trace='admin')
            import traceback
            traceback.print_exc()
            continue