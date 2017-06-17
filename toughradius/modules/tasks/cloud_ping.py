#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
import datetime
from urllib import urlencode
from toughradius.toughlib import utils
import platform as pf
from twisted.internet import defer
from cyclone import httpclient
from toughradius.toughlib import dispatch, logger
from toughradius.modules import taskd, models
from toughradius.common import tools
from toughradius.toughlib.dbutils import make_db
from toughradius import __version__
from toughradius.modules.tasks.task_base import TaseBasic

class ToughCloudPingTask(TaseBasic):
    __name__ = 'toughcloud-ping'

    def __init__(self, taskd, **kwargs):
        TaseBasic.__init__(self, taskd, **kwargs)

    def get_next_interval(self):
        return 300

    def first_delay(self):
        return self.get_next_interval()

    @defer.inlineCallbacks
    def process(self, *args, **kwargs):
        next_interval = self.get_next_interval()
        user_total = 0
        online_total = 0
        with make_db(self.db) as db:
            try:
                user_total = db.query(models.TrAccount).count()
                online_total = db.query(models.TrOnline).count()
            except Exception as err:
                pass

        try:
            api_url = 'http://www.toughcloud.net/api/v1/ping'
            api_token = yield tools.get_sys_token()
            params = dict(token=api_token, app='toughee', ver=__version__, release=os.environ.get('LICENSE_TYPE', 'taurusxee'), unum=user_total, onum=online_total, dist=pf.linux_distribution())
            param_str = urlencode(params)
            resp = yield httpclient.fetch(api_url + '?' + param_str, followRedirect=True)
            logger.info('toughcloud ping resp code: %s' % resp.code)
        except Exception as err:
            logger.error(err)

        defer.returnValue(next_interval)


taskd.TaskDaemon.__taskclss__.append(ToughCloudPingTask)