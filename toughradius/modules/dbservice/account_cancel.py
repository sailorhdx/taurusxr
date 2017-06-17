#!/usr/bin/env python
# coding=utf-8
import traceback
from toughradius.modules.settings import *
from hashlib import md5
from toughradius.modules import models
from toughradius.toughlib import utils, dispatch, redis_cache, logger
from toughradius.modules.events.settings import ACCOUNT_CHANNEL_EVENT
from toughradius.modules.events.settings import UNLOCK_ONLINE_EVENT
from toughradius.modules.dbservice import BaseService
from toughradius.modules.dbservice import logparams
from toughradius.common import tools
from toughradius.toughlib.btforms import rules
from toughradius.modules.events import settings as evset

class AccountCancel(BaseService):

    @logparams
    def cancel(self, formdata, **kwargs):
        """用户销户，将用户状态设置为销户状态，账号不可用，不删除用户数据，数据保留用做查询统计。

        :param formdata:   用户销户参数表
        :type formdata:    dict
        
        formdata params:
        
        :param account_number:   用户账号
        :type account_number:    string
        :param operate_desc:    操作描述
        :type operate_desc:     string
        :param fee_value:    费用金额(元) x.xx
        :type fee_value:     string
        """
        try:
            account_number = self.parse_arg(formdata, 'account_number', rule=rules.not_null)
            fee_value = self.parse_arg(formdata, 'fee_value', rule=rules.is_rmb)
            operate_desc = self.parse_arg(formdata, 'operate_desc', defval='')
            account = self.db.query(models.TrAccount).get(account_number)
            if account.status != 1:
                raise ValueError(u'无效用户状态')
            accept_log = models.TrAcceptLog()
            accept_log.id = utils.get_uuid()
            accept_log.accept_type = 'cancel'
            accept_log.accept_source = 'console'
            accept_log.account_number = account_number
            accept_log.accept_time = utils.get_currtime()
            accept_log.operator_name = self.operator.operator_name
            accept_log.accept_desc = u'用户销户退费%s(元);%s' % (fee_value, utils.safeunicode(operate_desc))
            accept_log.stat_year = accept_log.accept_time[0:4]
            accept_log.stat_month = accept_log.accept_time[0:7]
            accept_log.stat_day = accept_log.accept_time[0:10]
            accept_log.sync_ver = tools.gen_sync_ver()
            self.db.add(accept_log)
            old_expire_date = account.expire_date
            order = models.TrCustomerOrder()
            order.id = utils.get_uuid()
            order.order_id = utils.gen_order_id()
            order.customer_id = account.customer_id
            order.product_id = account.product_id
            order.account_number = account_number
            order.order_fee = 0
            order.actual_fee = -utils.yuan2fen(fee_value)
            order.pay_status = 1
            order.order_source = 'console'
            order.accept_id = accept_log.id
            order.create_time = utils.get_currtime()
            order.order_desc = accept_log.accept_desc
            order.stat_year = order.create_time[0:4]
            order.stat_month = order.create_time[0:7]
            order.stat_day = order.create_time[0:10]
            order.sync_ver = tools.gen_sync_ver()
            self.db.add(order)
            account.status = 3
            agency_id = self.db.query(models.TrCustomer.agency_id).filter_by(customer_id=account.customer_id).scalar()
            if agency_id:
                agency = self.db.query(models.TrAgency).get(agency_id)
                sfee = decimal.Decimal(order.actual_fee) * decimal.Decimal(agency.share_rate) / decimal.Decimal(100)
                sfee = int(sfee.to_integral_value())
                if agency.amount < sfee:
                    raise ValueError(u'代理商预存款余额不足')
                agency.amount -= -sfee
                aorder = models.TrAgencyOrder()
                aorder.id = utils.get_uuid()
                aorder.agency_id = agency.id
                aorder.fee_type = 'sharecost'
                aorder.fee_value = sfee
                aorder.fee_total = agency.amount
                aorder.fee_desc = u'用户 %s 销户退费分摊(%s%%) %s 元' % (account_number, agency.share_rate, utils.fen2yuan(aorder.fee_value))
                aorder.create_time = utils.get_currtime()
                order.sync_ver = tools.gen_sync_ver()
                self.db.add(aorder)
            self.db.commit()
            dispatch.pub(ACCOUNT_CHANNEL_EVENT, account.account_number, async=True)
            dispatch.pub(redis_cache.CACHE_DELETE_EVENT, account_cache_key(account.account_number), async=True)
            for online in self.db.query(models.TrOnline).filter_by(account_number=account.account_number):
                dispatch.pub(UNLOCK_ONLINE_EVENT, online.account_number, online.nas_addr, online.acct_session_id, async=True)

            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户销户失败:%s, %s' % (utils.safeunicode(err.message), err.__class__)
            logger.error(self.last_error, tag='account_cancel_error', username=formdata.get('account_number'))
            return False
