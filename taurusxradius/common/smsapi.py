#!/usr/bin/env python
# coding=utf-8
import time
import json
import base64
from urllib import urlencode
from taurusxradius.taurusxlib import apiutils
from taurusxradius.taurusxlib import logger
from taurusxradius.taurusxlib import utils
from taurusxradius.taurusxlib.smsutils import smscn
from taurusxradius.taurusxlib.smsutils import qcloud
from taurusxradius.taurusxlib.smsutils import sendcloud
from taurusxradius.taurusxlib.smsutils import taurusxcloud
from taurusxradius.taurusxlib.btforms import rules
from cyclone import httpclient
from twisted.internet import defer

class SmsApi(object):

    def __init__(self):
        self.gateways = ['taurusxcloud',
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
        elif gateway == 'taurusxcloud':
            self.smscalls[gateway] = taurusxcloud.SmsApi(apikey, apisecret)
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