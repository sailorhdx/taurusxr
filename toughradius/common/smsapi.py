#!/usr/bin/env python
# coding=utf-8
import time
import json
import base64
from urllib import urlencode
from toughradius.toughlib import apiutils
from toughradius.toughlib import logger
from toughradius.toughlib import utils
from toughradius.toughlib.smsutils import smscn
from toughradius.toughlib.smsutils import qcloud
from toughradius.toughlib.smsutils import sendcloud
from toughradius.toughlib.smsutils import toughcloud
from toughradius.toughlib.btforms import rules
from cyclone import httpclient
from twisted.internet import defer

class SmsApi(object):

    def __init__(self):
        self.gateways = ['toughcloud',
         'smscn',
         'qcloud',
         'sendcloud']
        self.smscalls = {}

    def get_instance(self, gateway, apikey, apisecret):
        if gateway in self.smscalls:
            return self.smscalls[gateway]
        if gateway == 'smscn':
            self.smscalls[gateway] = smscn.SmsApi(apikey, apisecret)
        elif gateway == 'qcloud':
            self.smscalls[gateway] = qcloud.SmsApi(apikey, apisecret)
        elif gateway == 'sendcloud':
            self.smscalls[gateway] = sendcloud.SmsApi(apikey, apisecret)
        elif gateway == 'toughcloud':
            self.smscalls[gateway] = toughcloud.SmsApi(apikey, apisecret)
        return self.smscalls.get(gateway)

    @defer.inlineCallbacks
    def send_sms(self, gateway, apikey, apisecret, sendphone, tplid, args = [], kwargs = {}):
        if gateway not in self.gateways:
            raise ValueError(u'gateway [%s] not support' % gateway)
        if not rules.is_mobile.valid(sendphone):
            raise ValueError(u'sendsms: %s mobile format error' % sendphone)
        try:
            api = self.get_instance(gateway, apikey, apisecret)
            resp = yield api.send_sms(sendphone, tplid, args=args, kwargs=kwargs)
            defer.returnValue(resp)
        except Exception as err:
            logger.exception(err)
            defer.returnValue(False)


_smsapi = SmsApi()
send_sms = _smsapi.send_sms