#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils, httpclient
from toughradius.toughlib import dispatch, logger
from toughradius.modules import models
from toughradius.toughlib.dbutils import make_db
from toughradius.modules.tasks.task_base import TaseBasic
from twisted.internet import reactor
import datetime
from urllib import quote
from toughradius.modules import taskd

class ExpireNotifyTask(TaseBasic):
    __name__ = 'wechat-expire-notify'

    def get_next_interval(self):
        return 86400

    def first_delay(self):
        return self.get_next_interval()

    def process(self, *args, **kwargs):
        self.logtimes()
        next_interval = self.get_next_interval()
        try:
            logger.info('start process wechat_notify task')
            _ndays = self.get_param_value('expire_notify_days')
            with make_db(self.db) as db:
                _now = datetime.datetime.now()
                _date = (datetime.datetime.now() + datetime.timedelta(days=int(_ndays))).strftime('%Y-%m-%d')
                expire_query = db.query(models.TrAccount).filter(models.TrAccount.customer_id == models.TrCustomer.customer_id, models.TrAccount.expire_date <= _date, models.TrAccount.expire_date >= _now.strftime('%Y-%m-%d'), models.TrAccount.status == 1)
                logger.info('wechat_notify total: %s' % expire_query.count())
                for account in expire_query:
                    dispatch.pub('wechat_account_expire', account.account_number, async=False)

            logger.info(u'微信到期通知任务已执行(%s个已通知)。下次执行还需等待 %s' % (expire_query.count(), self.format_time(next_interval)), trace='task')
        except Exception as err:
            logger.info(u'微信到期通知任务执行失败，%s。下次执行还需等待 %s' % (repr(err), self.format_time(next_interval)), trace='task')

        return next_interval


taskd.TaskDaemon.__taskclss__.append(ExpireNotifyTask)