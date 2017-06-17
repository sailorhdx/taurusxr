#!/usr/bin/env python
# coding=utf-8

import httplib
import json
import hashlib
import random
import time
from twisted.internet import defer
from toughradius.toughlib import utils, logger
from cyclone import httpclient

class SmsApi:
    appid = 0
    appkey = ''
    url = 'https://yun.tim.qq.com/v5/tlssmssvr/sendsms'

    def __init__(self, appid, appkey, debug = True):
        self.appid = appid
        self.appkey = appkey
        self.debug = debug

    def calculate_sig(self, appkey, rnd, cur_time, phone_numbers):
        phone_numbers_string = phone_numbers[0]
        for i in range(1, len(phone_numbers)):
            phone_numbers_string += ',' + phone_numbers[i]

        return hashlib.sha256('appkey=' + appkey + '&random=' + str(rnd) + '&time=' + str(cur_time) + '&mobile=' + phone_numbers_string).hexdigest()

    def calculate_sig_for_templ_phone_numbers(self, appkey, rnd, cur_time, phone_numbers):
        """ \xe8\xae\xa1\xe7\xae\x97\xe5\xb8\xa6\xe6\xa8\xa1\xe6\x9d\xbf\xe5\x92\x8c\xe6\x89\x8b\xe6\x9c\xba\xe5\x8f\xb7\xe5\x88\x97\xe8\xa1\xa8\xe7\x9a\x84 sig """
        phone_numbers_string = phone_numbers[0]
        for i in range(1, len(phone_numbers)):
            phone_numbers_string += ',' + phone_numbers[i]

        return hashlib.sha256('appkey=' + appkey + '&random=' + str(rnd) + '&time=' + str(cur_time) + '&mobile=' + phone_numbers_string).hexdigest()

    def calculate_sig_for_templ(self, appkey, rnd, cur_time, phone_number):
        phone_numbers = [phone_number]
        return self.calculate_sig_for_templ_phone_numbers(appkey, rnd, cur_time, phone_numbers)

    @defer.inlineCallbacks
    def send_sms(self, phone_number, tplid, args = [], kwargs = {}):
        """ \xe6\x8c\x87\xe5\xae\x9a\xe6\xa8\xa1\xe6\x9d\xbf\xe5\x8d\x95\xe5\x8f\x91
                Args:
                    nation_code: \xe5\x9b\xbd\xe5\xae\xb6\xe7\xa0\x81\xef\xbc\x8c\xe5\xa6\x82 86 \xe4\xb8\xba\xe4\xb8\xad\xe5\x9b\xbd
                    phone_number: \xe4\xb8\x8d\xe5\xb8\xa6\xe5\x9b\xbd\xe5\xae\xb6\xe7\xa0\x81\xe7\x9a\x84\xe6\x89\x8b\xe6\x9c\xba\xe5\x8f\xb7
                    templ_id: \xe6\xa8\xa1\xe6\x9d\xbf id
                    params: \xe6\xa8\xa1\xe6\x9d\xbf\xe5\x8f\x82\xe6\x95\xb0\xe5\x88\x97\xe8\xa1\xa8\xef\xbc\x8c\xe5\xa6\x82\xe6\xa8\xa1\xe6\x9d\xbf {1}...{2}...{3}\xef\xbc\x8c\xe9\x82\xa3\xe4\xb9\x88\xe9\x9c\x80\xe8\xa6\x81\xe5\xb8\xa6\xe4\xb8\x89\xe4\xb8\xaa\xe5\x8f\x82\xe6\x95\xb0
                    sign: \xe7\xad\xbe\xe5\x90\x8d\xef\xbc\x8c\xe5\xa6\x82\xe6\x9e\x9c\xe5\xa1\xab\xe7\xa9\xba\xe4\xb8\xb2\xef\xbc\x8c\xe7\xb3\xbb\xe7\xbb\x9f\xe4\xbc\x9a\xe4\xbd\xbf\xe7\x94\xa8\xe9\xbb\x98\xe8\xae\xa4\xe7\xad\xbe\xe5\x90\x8d
                    extend: \xe6\x89\xa9\xe5\xb1\x95\xe7\xa0\x81\xef\xbc\x8c\xe5\x8f\xaf\xe5\xa1\xab\xe7\xa9\xba\xe4\xb8\xb2
                    ext: \xe6\x9c\x8d\xe5\x8a\xa1\xe7\xab\xaf\xe5\x8e\x9f\xe6\xa0\xb7\xe8\xbf\x94\xe5\x9b\x9e\xe7\x9a\x84\xe5\x8f\x82\xe6\x95\xb0\xef\xbc\x8c\xe5\x8f\xaf\xe5\xa1\xab\xe7\xa9\xba\xe4\xb8\xb2
                Returns:
                    json string { "result": xxxx, "errmsg": "xxxxx" ... }\xef\xbc\x8c\xe8\xa2\xab\xe7\x9c\x81\xe7\x95\xa5\xe7\x9a\x84\xe5\x86\x85\xe5\xae\xb9\xe5\x8f\x82\xe8\xa7\x81\xe5\x8d\x8f\xe8\xae\xae\xe6\x96\x87\xe6\xa1\xa3
        \xe8\xaf\xb7\xe6\xb1\x82\xe5\x8c\x85\xe4\xbd\x93
        {
            "tel": {
                "nationcode": "86",
                "mobile": "13788888888"
            },
            "sign": "\xe8\x85\xbe\xe8\xae\xaf\xe4\xba\x91",
            "tpl_id": 19,
            "params": [
                "\xe9\xaa\x8c\xe8\xaf\x81\xe7\xa0\x81",
                "1234",
                "4"
            ],
            "sig": "fdba654e05bc0d15796713a1a1a2318c",
            "time": 1479888540,
            "extend": "",
            "ext": ""
        }
        \xe5\xba\x94\xe7\xad\x94\xe5\x8c\x85\xe4\xbd\x93
        {
            "result": 0,
            "errmsg": "OK",
            "ext": "",
            "sid": "xxxxxxx",
            "fee": 1
        }
                """
        rnd = random.randint(100000, 999999)
        cur_time = long(time.time())
        whole_url = self.url + '?sdkappid=' + str(self.appid) + '&random=' + str(rnd)
        data = {}
        tel = {'nationcode': 86,
         'mobile': phone_number}
        data['tel'] = tel
        data['tpl_id'] = tplid
        data['sign'] = ''
        data['sig'] = self.calculate_sig_for_templ(self.appkey, rnd, cur_time, phone_number)
        data['params'] = args
        data['time'] = cur_time
        data['extend'] = ''
        data['ext'] = ''
        resp = yield httpclient.fetch(whole_url, postdata=json.dumps(data))
        print dir(resp)
        if '200' != str(resp.code):
            defer.returnValue(True)
        else:
            ret = json.loads(resp.body)
            if self.debug:
                logger.info(ret)
            defer.returnValue(ret['result'] == 0)