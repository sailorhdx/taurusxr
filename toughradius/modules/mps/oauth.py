#!/usr/bin/env python
# coding=utf-8
import requests
import urllib
import base64
from toughradius.toughlib import logger
from toughradius.toughlib.permit import permit
from toughradius.modules.mps.base import BaseHandler

@permit.route('/mps/oauth')

class MpOAuthHandler(BaseHandler):

    def get(self):
        mps_apiurl = self.get_param_value('mps_apiurl')
        appid = self.get_param_value('mps_appid')
        openid = self.session.get('mps_openid')
        cbk = self.get_argument('cbk')
        if not openid:
            rurl = '%s/oauth/callback' % mps_apiurl
            _wx_url = self.mpsapi.wx_oauth_redirect_url(rurl, appid, cbk=cbk)
            logger.info('wx_openid_redirect ==> %s' % _wx_url)
            self.redirect(_wx_url, permanent=False)
        else:
            self.redirect(cbk, permanent=False)


@permit.route('/mps/oauth/callback')

class MpOAuthCBKHandler(BaseHandler):

    def get(self):
        mps_apiurl = self.get_param_value('mps_apiurl')
        cbk = self.get_argument('cbk')
        appid = self.get_param_value('mps_appid')
        appsecret = self.get_param_value('mps_apisecret')
        code = self.get_argument('code')
        wx_resp = self.mpsapi.get_oauth_token(appid, appsecret, code)
        logger.info('get_oauth_token %s' % wx_resp)
        openid = wx_resp['openid']
        self.session['mps_openid'] = openid
        self.session.save()
        self.redirect(cbk, permanent=False)