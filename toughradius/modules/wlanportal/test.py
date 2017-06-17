#!/usr/bin/env python
# coding=utf-8
import cyclone.web
from urllib import urlencode
from twisted.internet import reactor, defer
from toughradius.toughlib import logger, utils, dispatch
from toughradius.toughlib.permit import permit
from toughradius.toughlib import db_cache as cache
from toughradius.toughlib.dbengine import get_engine
from toughradius.modules.wlanportal.base import BaseHandler

@permit.route('/test')

class PortalForwardHandler(BaseHandler):

    def get(self, *args, **kwargs):
        logger.info(utils.safeunicode(self.request.query))
        wlan_params = {'wlanuserip': self.get_argument('userip', self.request.remote_ip),
         'wlanusername': self.get_argument('username', 'test'),
         'wlanacip': self.get_argument('wlanacip', '127.0.0.1'),
         'ssid': self.get_argument('ssid', 'default'),
         'wlanusermac': self.get_argument('wlanusermac', '00-00-00-00-00'),
         'wlanapmac': self.get_argument('wlanapmac', '00-00-00-00-00'),
         'wlanuserfirsturl': self.get_argument('wlanuserfirsturl', '/'),
         'callback': self.get_argument('callback', ''),
         'vendortype': self.get_argument('vendortype', '')}
        logger.info(utils.safeunicode(wlan_params))
        url = '/login?' + urlencode(wlan_params)
        logger.info('portal forward to : %s' % url)
        self.redirect(url, permanent=False)