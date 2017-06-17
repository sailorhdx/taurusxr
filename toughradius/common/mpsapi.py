#!/usr/bin/env python
# coding=utf-8
import requests
import json
import urllib
import time
from toughradius.toughlib import logger
from twisted.internet import defer
from cyclone import httpclient

class MpsApi:

    def __init__(self, cache = None):
        self.cache = cache
        self.api_address = 'https://api.weixin.qq.com'
        self.oauth_address = 'https://open.weixin.qq.com'
        self.upload_address = 'http://file.api.weixin.qq.com'

    def wx_oauth_token_url(self, appid, appsecret, code):
        _url = '%s/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code'
        return _url % (self.api_address,
         appid,
         appsecret,
         code)

    def wx_oauth_redirect_url(self, oauthbak_url, appid, **params):
        _url = '%s/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&scope=snsapi_base&state=STATE#wechat_redirect'
        _params = params and '?' + urllib.urlencode(params) or ''
        return _url % (self.oauth_address, appid, urllib.quote_plus(oauthbak_url) + urllib.quote_plus(_params))

    def wx_gettoken_url(self, appid, appsecret):
        return '%s/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % (self.api_address, appid, appsecret)

    def get_oauth_token(self, appid, appsecret, code):
        wx_url = self.wx_oauth_token_url(appid, appsecret, code)
        wx_resp = requests.get(wx_url)
        return json.loads(wx_resp.text)

    def get_access_token(self, appid, appsecret):
        _cache_key = 'toughee.%s.mps_access_token' % appid
        mps_access_token = self.cache.get(_cache_key)
        if not mps_access_token:
            resp = requests.get(self.wx_gettoken_url(appid, appsecret))
            json_obj = resp.json()
            mps_access_token = json_obj.get('access_token')
            if mps_access_token:
                logger.info('get a new access_token: ' + mps_access_token)
                self.cache.set(_cache_key, mps_access_token, 6000)
        return (mps_access_token, time.time() + 6000)

    def set_access_token(self, access_token, access_token_expires_at):
        pass