#!/usr/bin/env python
# coding=utf-8

import sys
import json
import time
import os
from hashlib import md5
from cyclone import httpclient
from urllib import urlencode
from toughradius.toughlib import utils, logger
from toughradius.toughlib.storage import Storage
from twisted.internet import reactor, defer

class SmsApi(object):
    url = 'http://sendcloud.sohu.com/smsapi/send'

    def __init__(self, apiuser, apikey, debug = True):
        self.apiuser = apiuser
        self.apikey = apikey
        self.debug = debug

    def make_message(self, param):
        param_keys = list(param.keys())
        param_keys.sort()
        param_str = ''
        for key in param_keys:
            param_str += key + u'=' + utils.safeunicode(param[key]) + u'&'

        param_str = param_str[:-1]
        sign_str = self.apikey + u'&' + param_str + u'&' + self.apikey
        param['signature'] = md5(utils.safestr(sign_str)).hexdigest()
        return param

    @defer.inlineCallbacks
    def send_sms(self, phone, tplid, args = [], kwargs = {}):
        if self.debug:
            logger.info('send sms to phone %s' % phone)
        params = {'%{0}%'.format(k):v for k, v in kwargs.iteritems()}
        param = self.make_message({'smsUser': self.apiuser,
         'templateId': tplid,
         'msgType': 0,
         'phone': phone,
         'vars': utils.safestr(json.dumps(params, ensure_ascii=False))})
        if self.debug:
            logger.info(param)
        resp = yield httpclient.fetch(SmsApi.url, postdata=urlencode(param))
        ret = json.loads(resp.body)
        if self.debug:
            logger.info(ret)
        if ret['statusCode'] == 200:
            defer.returnValue(True)
        else:
            _err = 'Send sms failure, statusCode=%s,message=%s' % (ret['statusCode'], utils.safestr(ret['message']))
            logger.error(_err, trace='event')
            defer.returnValue(False)