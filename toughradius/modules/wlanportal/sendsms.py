#!/usr/bin/env python
# coding=utf-8
import time
import json
import cyclone.web
from twisted.internet import reactor, defer
from toughradius.toughlib import logger, utils, dispatch
from toughradius.toughlib.permit import permit
from toughradius.modules.wlanportal.base import BaseHandler
from toughradius.modules.dbservice.customer_add import CustomerAdd
from toughradius.common import tools
from toughradius.common import smsapi
from twisted.internet import reactor, defer
from cyclone import httpclient

@permit.route('/sendsms')

class SendSmsHandler(BaseHandler):

    @defer.inlineCallbacks
    def get(self):
        yield self.post()

    @defer.inlineCallbacks
    def post(self):
        try:
            phone = self.get_argument('phone')
            domain = self.get_argument('domain')
            last_send = self.session.get('sms_last_send', 0)
            if last_send > 0:
                sec = int(time.time()) - last_send
                if sec < 60:
                    self.render_json(code=1, msg=u'还需等待%s秒' % sec)
                    return
            self.session['sms_last_send'] = int(time.time())
            self.session.save()
            vcode = str(time.time()).replace('.', '')[-6:]
            gateway = self.get_param_value('sms_gateway')
            apikey = self.get_param_value('sms_api_user')
            apisecret = self.get_param_value('sms_api_pwd')
            resp = yield smsapi.send_vcode(gateway, apikey, apisecret, phone, vcode)
            cmanager = CustomerAdd(self.db, self.aes, config=self.settings.config)
            customer = cmanager.add_wlan_user(domain, phone, vcode, u'hotspot sms verify join')
            if not customer:
                logger.error(cmanager.last_error)
                self.render_json(code=1, msg=u'自动注册失败')
                return
            self.render_json(code=0, msg='ok')
        except Exception as err:
            logger.exception(err)
            self.render_json(code=1, msg=u'发送短信失败')