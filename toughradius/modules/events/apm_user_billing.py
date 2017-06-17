#!/usr/bin/env python
# coding=utf-8
import datetime
from toughradius.toughlib import utils, dispatch
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib import logger
from toughradius.modules import models
from toughradius.modules.events.event_basic import BasicEvent
from toughradius.common import tools
import decimal

class ApmBillingEvent(BasicEvent):

    def event_apm_user_billing(self, account_number):
        logger.info(u'用户[%s]后付费自动出账任务执行' % account_number)
        with make_db(self.db) as db:
            try:
                account = db.query(models.TrAccount).get(account_number)
                product = db.query(models.TrProduct).get(account.product_id)
                fee_precision = self.get_param_value('billing_fee_precision', 'fen')
                if not product:
                    logger.error(u'执行后付费包月自动出账时，用户[%s]资费id[%s]不存在' % (account_number, product_id))
                    return
                accept_log = models.TrAcceptLog()
                accept_log.id = utils.get_uuid()
                accept_log.accept_type = 'apm_bill'
                accept_log.accept_source = 'task'
                accept_log.account_number = account_number
                accept_log.accept_time = utils.get_currtime()
                accept_log.operator_name = 'admin'
                accept_log.accept_desc = u'用户[%s]后付费包月自动出账, ' % account_number
                accept_log.stat_year = accept_log.accept_time[0:4]
                accept_log.stat_month = accept_log.accept_time[0:7]
                accept_log.stat_day = accept_log.accept_time[0:10]
                accept_log.sync_ver = tools.gen_sync_ver()
                self.db.add(accept_log)
                order = models.TrCustomerOrder()
                order.order_id = utils.get_uuid()
                order.customer_id = account.customer_id
                order.product_id = product.id
                order.account_number = account_number
                order.order_fee = product.fee_price
                order_bill_fee = product.fee_price
                order_bill_days = 30
                per_day_fee = decimal.Decimal(product.fee_price) / order_bill_days
                per_day_fee_yuan = utils.fen2yuan(int(per_day_fee.to_integral_value()))
                this_month_start_str = datetime.datetime.now().strftime('%Y-%m-01 %H:%M:%S')
                this_month_start = datetime.datetime.strptime(this_month_start_str, '%Y-%m-%d %H:%M:%S')
                pre_month_start_str = utils.add_months(datetime.datetime.now(), -1).strftime('%Y-%m-01 00:00:00')
                pre_month_start = datetime.datetime.strptime(pre_month_start_str, '%Y-%m-%d %H:%M:%S')
                pre_month_end = this_month_start - datetime.timedelta(days=1)
                pre_month_days = (pre_month_end - pre_month_start).days + 1
                user_create_time = datetime.datetime.strptime(account.create_time, '%Y-%m-%d %H:%M:%S')
                if user_create_time > pre_month_start:
                    order_bill_days = (pre_month_end - user_create_time).days
                    per_day_fee = decimal.Decimal(product.fee_price) / decimal.Decimal(pre_month_days)
                    per_day_fee_yuan = utils.fen2yuan(int(per_day_fee.to_integral_value()))
                    order_bill_fee = int((per_day_fee * order_bill_days).to_integral_value())
                if fee_precision == 'yuan':
                    order_bill_fee = int((decimal.Decimal(order_bill_fee) / decimal.Decimal(100)).to_integral_value()) * 100
                order.actual_fee = order_bill_fee
                order.pay_status = 0
                order.accept_id = accept_log.id
                order.order_source = accept_log.accept_source
                order.create_time = account.create_time
                order.order_desc = u'用户后付费账单：{0}(日均价={1}/{2}) x {3}(使用天数) '.format(per_day_fee_yuan, utils.fen2yuan(product.fee_price), pre_month_days, order_bill_days)
                order.stat_year = order.create_time[0:4]
                order.stat_month = order.create_time[0:7]
                order.stat_day = order.create_time[0:10]
                order.sync_ver = tools.gen_sync_ver()
                self.db.add(order)
                self.db.commit()
                logger.info(u'用户[%s]后付费出账完成' % account_number, trace='event')
            except Exception as err:
                logger.exception(err)
                logger.error(u'用户[%s]后付费出账失败' % account_number, trace='event')


def __call__(dbengine = None, mcache = None, aes = None, **kwargs):
    return ApmBillingEvent(dbengine=dbengine, mcache=mcache, aes=aes, **kwargs)