#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
import datetime
from taurusxradius.taurusxlib import utils
from taurusxradius.taurusxlib import dispatch, logger
from taurusxradius.taurusxlib.dbutils import make_db
from taurusxradius.modules import models
from taurusxradius.taurusxlib.db_backup import DBBackup
from taurusxradius.modules.tasks.task_base import TaseBasic
from twisted.internet import reactor
from taurusxradius.modules import taskd

class ClearBillingTask(TaseBasic):
    __name__ = 'billing-clean'

    def __init__(self, taskd, **kwargs):
        TaseBasic.__init__(self, taskd, **kwargs)

    def get_next_interval(self):
        return 86400

    def first_delay(self):
        return 120

    def process(self, *args, **kwargs):
        self.logtimes()
        next_interval = self.get_next_interval()
        with make_db(self.db) as db:
            try:
                td = datetime.timedelta(days=7)
                _now = datetime.datetime.now()
                edate = (_now - td).strftime('%Y-%m-%d 23:59:59')
                db.query(models.TrBilling).filter(models.TrBilling.create_time < edate).delete()
                db.commit()
                logger.info(u'计费缓存数据清理完成,下次执行还需等待 %s' % self.format_time(next_interval), trace='task')
            except Exception as err:
                logger.info(u'计费缓存数据清理失败,%s, 下次执行还需等待 %s' % (repr(err), self.format_time(next_interval)), trace='task')
                logger.exception(err)

        return next_interval


taskd.TaskDaemon.__taskclss__.append(ClearBillingTask)