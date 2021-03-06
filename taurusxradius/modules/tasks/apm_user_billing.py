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
from taurusxradius.modules.tasks.task_base import TaseBasic
from twisted.internet import reactor
from taurusxradius.modules import taskd
from taurusxradius.modules.settings import APMonth

class APmfUserRewTask(TaseBasic):
    __name__ = 'apm-user-billing'

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
                uquery = db.query(models.TrAccount).filter(models.TrAccount.product_id == models.TrProduct.id, models.TrAccount.status == 1, models.TrProduct.product_policy == APMonth, models.TrAccount.create_time < cmonth + '-01 00:00:00')
                for account in uquery:
                    alog = db.query(models.TrAcceptLog).filter(models.TrAcceptLog.accept_type == 'apm_bill', models.TrAcceptLog.account_number == account.account_number, models.TrAcceptLog.accept_time >= cmonth + '-01 00:00:00')
                    if alog.count() == 0:
                        rets = dispatch.pub('apm_user_billing', account.account_number, async=True)

            except Exception as err:
                logger.info(u'用户后付费包月自动出账执行失败,%s, 下次执行还需等待 %s' % (repr(err), self.format_time(next_interval)), trace='task')
                logger.exception(err)

        return next_interval


taskd.TaskDaemon.__taskclss__.append(APmfUserRewTask)