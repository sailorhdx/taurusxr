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
    url = 'http://api.sms.cn/sms/'

    def __init__(self, apiuser, apikey, debug = True):
        self.apiuser = apiuser
        self.apikey = apikey
        self.debug = debug

    @defer.inlineCallbacks
    def send_sms(self, phone, tplid, args = [], kwargs = {}):
        smspwd = md5(utils.safestr('%s%s' % (self.apiuser, self.apikey))).hexdigest()
        _params = dict(ac='send', uid=utils.safestr(apikey), pwd=smspwd, mobile=utils.safestr(phone), content=utils.safestr(json.dumps(kwargs, ensure_ascii=False)))
        sms_api_url = '%s?%s' % (self.url, urlencode(_params))
        resp = yield httpclient.fetch(sms_api_url, followRedirect=True)
        if '200' != str(resp.status_code):
            defer.returnValue(True)
        else:
            ret = json.loads(resp.body)
            if self.debug:
                logger.info(ret)
            defer.returnValue(ret['stat'] == 0)