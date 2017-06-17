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
from toughradius.modules.tasks.task_base import TaseBasic
from twisted.internet import reactor
from toughradius.modules import taskd
from toughradius.modules.settings import PPMFlows

class PPmfUserRewTask(TaseBasic):
    __name__ = 'ppmf-user-renew'

    def __init__(self, taskd, **kwargs):
        TaseBasic.__init__(self, taskd, **kwargs)

    def get_next_interval(self):
        return 10

    def first_delay(self):
        return self.get_next_interval()

    def process(self, *args, **kwargs):
        self.logtimes()
        next_interval = self.get_next_interval()
        billtask_last_day = int(self.get_param_value('billtask_last_day', 3))
        if billtask_last_day > 28:
            billtask_last_day = 28
        _now = datetime.datetime.now()
        if _now.day > billtask_last_day:
            return next_interval
        cmonth = _now.strftime('%Y-%m')
        with make_db(self.db) as db:
            try:
                uquery = db.query(models.TrAccount).filter(models.TrAccount.product_id == models.TrProduct.id, models.TrAccount.balance > 0, models.TrAccount.status == 1, models.TrProduct.product_policy == PPMFlows, models.TrAccount.create_time < cmonth + '-01 00:00:00')
                for account in uquery:
                    alog = db.query(models.TrAcceptLog).filter(models.TrAcceptLog.accept_type == 'auto_renew', models.TrAcceptLog.account_number == account.account_number, models.TrAcceptLog.accept_time >= cmonth + '-01 00:00:00')
                    if alog.count() == 0:
                        rets = dispatch.pub('ppmf_user_renew', account.account_number, account.product_id)

            except Exception as err:
                next_interval = 120
                logger.info(u'预付费流量包月续费执行失败,%s, 下次执行还需等待 %s' % (repr(err), self.format_time(next_interval)), trace='task')
                logger.exception(err)

        return next_interval


taskd.TaskDaemon.__taskclss__.append(PPmfUserRewTask)