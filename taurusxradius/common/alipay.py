#!/usr/bin/env python
# coding=utf-8
import types
from urllib import urlencode
from hashlib import md5
import requests
EVENT_SETUP = 'alipay_setup'

class Settings(dict):

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError, k

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError, k

    def __repr__(self):
        return '<Settings ' + dict.__repr__(self) + '>'


class AliPay:
    GATEWAY = 'https://mapi.alipay.com/gateway.do?'

    def __init__(self, settings = {}, logger = None):
        self.settings = settings
        self.logger = logger

    def event_alipay_setup(self, settings):
        self.settings = settings

    def safestr(self, val, errors = 'strict'):
        encoding = self.settings.get('ALIPAY_INPUT_CHARSET', 'utf-8')
        if val is None:
            return ''
        elif isinstance(val, unicode):
            return val.encode('utf-8', errors)
        elif isinstance(val, str):
            return val.decode('utf-8', errors).encode(encoding, errors)
        elif isinstance(val, (int, float)):
            return str(val)
        elif isinstance(val, Exception):
            return ' '.join([ self.safestr(arg, encoding, errors) for arg in val ])
        else:
            try:
                return str(val)
            except:
                return unicode(val).encode(encoding, errors)

            return val

    def make_sign(self, **msg):
        ks = msg.keys()
        ks.sort()
        sign_str = '&'.join([ '%s=%s' % (k, msg[k]) for k in ks ])
        if 'MD5' == self.settings.ALIPAY_SIGN_TYPE:
            return md5(sign_str + self.safestr(self.settings.ALIPAY_KEY)).hexdigest()
        raise Exception('not support sign type %s' % settings.ALIPAY_SIGN_TYPE)

    def check_sign(self, **msg):
        if 'sign' not in msg:
            return False
        params = {self.safestr(k):self.safestr(msg[k]) for k in msg if k not in ('sign', 'sign_type')}
        local_sign = self.make_sign(**params)
        return msg['sign'] == local_sign

    def make_request_url(self, **params):
        params.pop('sign', None)
        params.pop('sign_type', None)
        _params = {self.safestr(k):self.safestr(v) for k, v in params.iteritems() if v not in ('', None)}
        _params['sign'] = self.make_sign(**_params)
        _params['sign_type'] = self.settings.ALIPAY_SIGN_TYPE
        return AliPay.GATEWAY + urlencode(_params)

    def create_direct_pay_by_user(self, tn, subject, body, total_fee, notify_path = '', return_path = ''):
        params = {}
        params['service'] = 'create_direct_pay_by_user'
        params['payment_type'] = '1'
        params['partner'] = self.settings.ALIPAY_PARTNER
        params['seller_email'] = self.settings.ALIPAY_SELLER_EMAIL
        params['return_url'] = self.settings.ALIPAY_RETURN_URL + return_path
        params['notify_url'] = self.settings.ALIPAY_NOTIFY_URL + notify_path
        params['_input_charset'] = self.settings.ALIPAY_INPUT_CHARSET
        params['show_url'] = self.settings.ALIPAY_SHOW_URL
        params['out_trade_no'] = tn
        params['subject'] = subject
        params['body'] = body
        params['total_fee'] = total_fee
        params['paymethod'] = 'directPay'
        params['defaultbank'] = ''
        params['anti_phishing_key'] = ''
        params['exter_invoke_ip'] = ''
        params['buyer_email'] = ''
        params['extra_common_param'] = ''
        params['royalty_type'] = ''
        params['royalty_parameters'] = ''
        return self.make_request_url(**params)

    def notify_verify(self, request):
        if not self.check_sign(**request):
            self.logger.error('check_sign failure')
            return False
        params = {}
        params['partner'] = self.settings.ALIPAY_PARTNER
        params['notify_id'] = request.get('notify_id', '')
        if self.settings.ALIPAY_TRANSPORT == 'https':
            params['service'] = 'notify_verify'
            gateway = 'https://mapi.alipay.com/gateway.do'
        else:
            gateway = 'http://notify.alipay.com/trade/notify_query.do'
        try:
            veryfy_result = requests.get(gateway + '?' + urlencode(params)).text
        except:
            veryfy_result = requests.get(gateway + '?' + urlencode(params), verify=False).text

        self.logger.info('veryfy_result:%s' % veryfy_result)
        return veryfy_result.lower().strip() == 'true'


if __name__ == '__main__':
    settings = Settings(ALIPAY_KEY='234234', ALIPAY_INPUT_CHARSET='utf-8', ALIPAY_PARTNER='234', ALIPAY_SELLER_EMAIL='payment@34.com', ALIPAY_SIGN_TYPE='MD5', ALIPAY_RETURN_URL='', ALIPAY_NOTIFY_URL='', ALIPAY_SHOW_URL='', ALIPAY_TRANSPORT='https')
    alipay = AliPay(settings)
    params = {}
    params['service'] = 'create_direct_pay_by_user'
    params['payment_type'] = '1'
    params['aaaa'] = u'\u597d'
    print alipay.make_request_url(**params)
    print alipay.create_direct_pay_by_user('2323525', u'\u963f\u58eb\u5927\u592b', u'\u5565\u6253\u6cd5\u662f\u5426', 0.01)