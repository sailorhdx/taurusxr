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
    __name__ = 'sms-expire-notify'

    def get_next_interval(self):
        try:
            notify_interval = int(self.get_param_value('sms_notify_interval', 1440)) * 60.0
            notify_time = self.get_param_value('sms_notify_time', None)
            if notify_time not in ('', None, '00:00'):
                notify_interval = utils.get_cron_interval(notify_time)
            return notify_interval
        except:
            return 120

        return

    def first_delay(self):
        return self.get_next_interval()

    def process(self, *args, **kwargs):
        self.logtimes()
        next_interval = self.get_next_interval()
        try:
            logger.info('start process mail_notify task')
            _enable = int(self.get_param_value('sms_notify_enable', 0))
            if not _enable:
                return 120.0
            _ndays = self.get_param_value('expire_notify_days')
            with make_db(self.db) as db:
                _now = datetime.datetime.now()
                _date = (datetime.datetime.now() + datetime.timedelta(days=int(_ndays))).strftime('%Y-%m-%d')
                expire_query = db.query(models.TrAccount.account_number, models.TrAccount.expire_date, models.TrCustomer.email, models.TrCustomer.mobile).filter(models.TrAccount.customer_id == models.TrCustomer.customer_id, models.TrAccount.expire_date <= _date, models.TrAccount.expire_date >= _now.strftime('%Y-%m-%d'), models.TrAccount.status == 1)
                logger.info('mail_notify total: %s' % expire_query.count())
                for account, expire, email, mobile in expire_query:
                    dispatch.pub('sms_account_expire', account, async=False)

            logger.info(u'Sms到期通知任务已执行(%s个已通知)。下次执行还需等待 %s' % (expire_query.count(), self.format_time(next_interval)), trace='task')
        except Exception as err:
            logger.info(u'Sms到期通知任务执行失败，%s。下次执行还需等待 %s' % (repr(err), self.format_time(next_interval)), trace='task')

        return next_interval


taskd.TaskDaemon.__taskclss__.append(ExpireNotifyTask)