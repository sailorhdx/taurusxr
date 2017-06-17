#!/usr/bin/env python
# coding=utf-8
import cyclone.web
from toughradius.toughlib import logger
from toughradius.toughlib import utils
from toughradius.toughlib import logger
from toughradius.toughlib.permit import permit
from hashlib import sha1
from cyclone.util import ObjectDict
from cyclone.options import options
from twisted.internet import defer
from toughradius.common import wxrouter
from toughradius.modules.mps.base import BaseHandler
from toughradius.modules import models
from wechat_sdk import WechatBasic
from wechat_sdk import WechatConf
import functools

@permit.route('/')

class HelloHandler(BaseHandler):

    def get(self):
        self.write('ok')


@permit.route('/MP_verify_Z677kYAea8jAjpEn.txt')

class VerifyHandler(BaseHandler):

    def get(self):
        self.write('Z677kYAea8jAjpEn')


@permit.route('/mps')

class IndexHandler(BaseHandler):
    """ 微信消息主要处理控制器 """
    WechatConfCachekey = 'toughee.wechat.conf.cache'

    def check_xsrf_cookie(self):
        """ 对于微信消息不做加密cookie处理 """
        pass

    def get_error_html(self, status_code = 500, **kwargs):
        """ 定制微信消息错误返回 """
        self.set_header('Content-Type', 'application/xml;charset=utf-8')
        self.write(self.wechat.response_text(u'回复h查看帮助。'))
        self.finish()

    def check_signature(self):
        """ 微信消息验签处理 """
        signature = self.get_argument('signature', '')
        timestamp = self.get_argument('timestamp', '')
        nonce = self.get_argument('nonce', '')
        return self.wechat.check_signature(signature=signature, timestamp=timestamp, nonce=nonce)

    def init_wechat(self):
        try:
            wechat_conf_cache = self.cache.get(self.WechatConfCachekey)
            if not wechat_conf_cache:
                token = self.get_param_value('mps_token')
                appid = self.get_param_value('mps_appid')
                appsecret = self.get_param_value('mps_apisecret')
                encrypt_mode = self.get_param_value('mps_encrypt_mode', 'normal')
                encoding_aes_key = self.get_param_value('mps_encoding_aes_key', '')
                wechat_conf_cache = dict(token=token, appid=appid, appsecret=appsecret, encrypt_mode=encrypt_mode, encoding_aes_key=encoding_aes_key)
                self.cache.set(self.WechatConfCachekey, wechat_conf_cache, expire=300)
            _c = wechat_conf_cache
            wechat_conf = WechatConf(token=_c['token'], appid=_c['appid'], appsecret=_c['appsecret'], encrypt_mode=_c['encrypt_mode'], encoding_aes_key=_c['encoding_aes_key'], access_token_getfunc=functools.partial(self.mpsapi.get_access_token, _c['appid'], _c['appsecret']), access_token_setfunc=self.mpsapi.set_access_token)
            self.wechat = WechatBasic(conf=wechat_conf)
        except Exception as err:
            logger.exception(err)

    def get(self):
        self.init_wechat()
        echostr = self.get_argument('echostr', '')
        if self.check_signature():
            self.write(echostr)
            logger.info('Signature check success.')
        else:
            logger.error('Signature check failed.')

    @defer.inlineCallbacks
    def post(self):
        """ 微信消息处理 """
        self.init_wechat()
        if not self.check_signature():
            logger.error('Signature check failed.')
            return
        try:
            self.set_header('Content-Type', 'application/xml;charset=utf-8')
            body = self.request.body
            self.wechat.parse_data(body)
            msg = self.wechat.get_message()
            logger.debug(u'message type %s from %s with %s' % (self.wechat.message.type, self.wechat.message.source, body.decode('utf-8')))
            response = yield wxrouter.dispatch(msg, gdata=self.application, wechat=self.wechat)
            logger.debug(u'Replied to %s with "%s"' % (self.wechat.message.source, response))
            self.write(response)
        except Exception as err:
            logger.exception(err)
            self.write('error')