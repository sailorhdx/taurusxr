#!/usr/bin/env python
# coding=utf-8

import sys
import json
import time
import os
from taurusxradius.taurusxlib import apiutils
from cyclone import httpclient
from urllib import urlencode
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.taurusxlib.storage import Storage
from twisted.internet import reactor, defer

class SmsApi(object):
    url = 'http://www.taurusxcloud.net/api/v1'

    def __init__(self, apiuser, apikey, debug = True):
        self.apiuser = apiuser
        self.apikey = apikey
        self.debug = debug

    @defer.inlineCallbacks
    def send_sms(self, phone, tplid, args = [], kwargs = {}):
        smsapiurl = '{0}/taurusxee/sendsms'.format(self.url)
        kwargs['apikey'] = self.apiuser
        kwargs['phone'] = phone
        kwargs['tplname'] = tplid
        kwargs['timestamp'] = long(time.time())
        kwargs['sign'] = apiutils.make_sign(self.apikey, kwargs.values())
        postdata = urlencode(kwargs)
        resp = yield httpclient.fetch(smsapiurl, postdata=postdata)
        ret = json.loads(resp.body)
        defer.returnValue(ret['code'] == 0)