#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils, logger, dispatch
from cyclone import httpclient
from hashlib import md5
from urllib import urlencode
from toughradius.modules import models
from toughradius.common import smsapi
from toughradius.modules.events.event_basic import BasicEvent

class SendSmsEvent(BasicEvent):

    def event_sendsms(self, sendphone, tplid, **params):
        gateway = self.get_param_value('sms_gateway')
        apikey = self.get_param_value('sms_api_user')
        apisecret = self.get_param_value('sms_api_pwd')
        try:
            smsapi.send_sms(gateway, apikey, apisecret, sendphone, tplid, **params)
        except Exception as err:
            logger.exception(err)


def __call__(dbengine = None, mcache = None, **kwargs):
    return SendSmsEvent(dbengine=dbengine, mcache=mcache, **kwargs)