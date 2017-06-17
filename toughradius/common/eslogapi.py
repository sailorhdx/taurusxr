#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils
from toughradius.toughlib import logger
from cyclone import httpclient
from toughradius.common import tools
from twisted.internet import reactor
from toughradius import __version__
import json
import time
import datetime
import base64
import traceback
import sys
try:
    import pytz
except:
    traceback.print_exc()

class EslogApi(object):

    def __init__(self, esconfig):
        self.apiurl = esconfig.apiurl
        self.apiuser = esconfig.apiuser
        self.apipwd = esconfig.apipwd
        self.index = esconfig.get('index', tools.get_sys_uuid())
        self.tz = pytz.timezone(esconfig.get('tz', 'Asia/Shanghai'))
        reactor.callLater(1.0, self.init_index)

    def init_index(self):
        try:
            puturl = '{0}/{1}'.format(self.apiurl, self.index)
            reqmsg = '{"mappings": {"taurusxr": {"_ttl": {"enabled": true,"default": "7d"}}}}'
            user_and_pwd = '{0}:{1}'.format(self.apiuser, self.apipwd)
            headers = {'Authorization': ['Basic {0}'.format(base64.b64encode(user_and_pwd))]}
            d = httpclient.fetch(puturl, postdata=reqmsg, headers=headers)
            d.addCallback(lambda r: logger.debug(r.body)).addErrback(lambda e: sys.stderr.write(repr(e)))
        except:
            traceback.print_exc()

    def send(self, **kwargs):
        try:
            _ctime = self.tz.localize(datetime.datetime.now())
            ttl = kwargs.pop('ttl', '7d')
            reqmsg = dict(ver=__version__, timestamp=_ctime.isoformat(), tag=kwargs.pop('tag', 'normal'))
            reqmsg.update(kwargs)
            puturl = '{0}/{1}/taurusxr?ttl={2}'.format(self.apiurl, self.index, ttl)
            user_and_pwd = '{0}:{1}'.format(self.apiuser, self.apipwd)
            headers = {'Authorization': ['Basic {0}'.format(base64.b64encode(user_and_pwd))]}
            postdata = utils.safestr(json.dumps(reqmsg, ensure_ascii=False))
            d = httpclient.fetch(puturl, postdata=postdata, headers=headers)
            d.addCallback(lambda r: logger.debug(r.body)).addErrback(lambda e: sys.stderr.write(repr(e)))
        except:
            traceback.print_exc()

    def event_syslog_trace(self, name, message, **kwargs):
        """ eslog trace event """
        if kwargs.pop('eslog', None) or name in ('error', 'exception'):
            self.send(topic=name, message=utils.safeunicode(message), **kwargs)
        return