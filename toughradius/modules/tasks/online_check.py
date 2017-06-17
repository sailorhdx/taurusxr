#!/usr/bin/env python
# coding=utf-8
import sys
import time
import datetime
from toughradius.toughlib import utils
from toughradius.toughlib import dispatch, logger
from toughradius.modules import models
from toughradius.toughlib.dbutils import make_db
from toughradius.modules.tasks.task_base import TaseBasic
from toughradius.modules.events.settings import CLEAR_ONLINE_EVENT
from twisted.internet import reactor
from toughradius.modules import taskd

class OnlineCheckTask(TaseBasic):
    __name__ = 'online-checks'

    def get_next_interval(self):
        return 30

    def first_delay(self):
        return 5

    def process(self, *args, **kwargs):
        self.logtimes()
        with make_db(self.db) as db:
            try:
                onlines = db.query(models.TrOnline)
                for online in onlines:
                    acct_start_time = datetime.datetime.strptime(online.acct_start_time, '%Y-%m-%d %H:%M:%S')
                    acct_session_time = online.billing_times
                    nowdate = datetime.datetime.now()
                    dt = nowdate - acct_start_time
                    online_times = dt.total_seconds()
                    max_interim_intelval = int(self.get_param_value('radius_acct_interim_intelval', 240))
                    if online_times - acct_session_time > max_interim_intelval + 30:
                        logger.info('online %s overtime, system auto clear this online' % online.account_number)
                        dispatch.pub(CLEAR_ONLINE_EVENT, online.account_number, online.nas_addr, online.acct_session_id, async=True)

            except Exception as err:
                db.rollback()
                logger.exception(err)

        return 30.0


taskd.TaskDaemon.__taskclss__.append(OnlineCheckTask)