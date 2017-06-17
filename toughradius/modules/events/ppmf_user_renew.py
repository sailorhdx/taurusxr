#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils, dispatch
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib import logger
from toughradius.modules import models
from toughradius.modules.events.event_basic import BasicEvent
from toughradius.common import tools

class PpmfRenewEvent(BasicEvent):

    def event_ppmf_user_renew(self, account_number, product_id):
        with make_db(self.db) as db:
            try:
                account = db.query(models.TrAccount).get(account_number)
                product = db.query(models.TrProduct).get(product_id)
                if not product:
                    logger.error(u'执行流量包月续费时，用户[%s]资费id[%s]不存在' % (account_number, product_id))
                    return
                if product.fee_price > account.balance:
                    logger.error(u'执行流量包月续费时，用户[%s]余额不足' % account_number)
                    return
                old_balance = account.balance
                old_flows = account.flow_length
                account.balance -= product.fee_price
                account.flow_length = product.fee_flows
                account.sync_ver = tools.gen_sync_ver()
                accept_log = models.TrAcceptLog()
                accept_log.id = utils.get_uuid()
                accept_log.accept_type = 'auto_renew'
                accept_log.accept_source = 'task'
                accept_log.account_number = account_number
                accept_log.accept_time = utils.get_currtime()
                accept_log.operator_name = 'admin'
                accept_log.accept_desc = u'用户[%s]流量包月套餐续费, 续费前余额为(%s)元,流量为(%s)G,续费后余额为(%s)元,流量为(%s)G' % (account_number,
                 utils.fen2yuan(old_balance),
                 utils.kb2gb(old_flows),
                 utils.fen2yuan(account.balance),
                 utils.kb2gb(account.flow_length))
                accept_log.stat_year = accept_log.accept_time[0:4]
                accept_log.stat_month = accept_log.accept_time[0:7]
                accept_log.stat_day = accept_log.accept_time[0:10]
                accept_log.sync_ver = tools.gen_sync_ver()
                self.db.add(accept_log)
                self.db.commit()
                logger.info(u'用户[%s]流量包月套餐续费完成' % account_number, trace='event')
            except Exception as err:
                logger.exception(err)
                logger.error(u'用户[%s]流量包月套餐续费失败' % account_number, trace='event')


def __call__(dbengine = None, mcache = None, aes = None, **kwargs):
    return PpmfRenewEvent(dbengine=dbengine, mcache=mcache, aes=aes, **kwargs)