#!/usr/bin/env python
# coding=utf-8
import os
import sys
import time
import datetime
from toughradius.toughlib import utils
from toughradius.toughlib import dispatch, logger
from toughradius.toughlib.dbutils import make_db
from toughradius.modules import models
from toughradius.toughlib.db_backup import DBBackup
from toughradius.modules.tasks.task_base import TaseBasic
from twisted.internet import reactor
from toughradius.modules import taskd

class ClearTicketTask(TaseBasic):
    __name__ = 'ticket-clean'

    def __init__(self, taskd, **kwargs):
        TaseBasic.__init__(self, taskd, **kwargs)

    def get_next_interval(self):
        return utils.get_cron_interval('04:00')

    def first_delay(self):
        return self.get_next_interval()

    def process(self, *args, **kwargs):
        self.logtimes()
        next_interval = self.get_next_interval()
        with make_db(self.db) as db:
            try:
                _days = int(self.get_param_value('system_ticket_expire_days', 30))
                td = datetime.timedelta(days=_days)
                _now = datetime.datetime.now()
                edate = (_now - td).strftime('%Y-%m-%d 23:59:59')
                db.query(models.TrTicket).filter(models.TrTicket.acct_stop_time < edate).delete()
                db.commit()
                logger.info(u'上网数据清理完成,下次执行还需等待 %s' % self.format_time(next_interval), trace='task')
            except Exception as err:
                logger.info(u'上网数据清理失败,%s, 下次执行还需等待 %s' % (repr(err), self.format_time(next_interval)), trace='task')
                logger.exception(err)

        return next_interval


taskd.TaskDaemon.__taskclss__.append(ClearTicketTask)