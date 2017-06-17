#!/usr/bin/env python
# coding=utf-8
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

class AccountChange(BaseService):

    @logparams
    def change(self, formdata, **kwargs):
        """用户资费变更

        :param formdata:   用户续费参数表
        :type formdata:    dict
        
        formdata params:
        
        :param account_number:   用户账号
        :type account_number:    string
        :param product_id:   变更后的资费ID
        :type product_id:    string
        :param expire_date:   变更后的到期时间 yyyy-mm-dd
        :type expire_date:    string
        :param balance:   变更后的余额 x.xx 元
        :type balance:    string
        :param time_length:   变更后的剩余时长-小时
        :type time_length:    string
        :param flow_length:   变更后的剩余流量-GB
        :type flow_length:    string
        :param add_value:   变更费用 x.xx 元
        :type add_value:    string
        :param operate_desc:   变更说明
        :type operate_desc:    string
        """
        try:
            account_number = self.parse_arg(formdata, 'account_number', rule=rules.not_null)
            product_id = self.parse_arg(formdata, 'product_id', rule=rules.not_null)
            expire_date = self.parse_arg(formdata, 'expire_date', rule=rules.is_date)
            balance = self.parse_arg(formdata, 'balance', rule=rules.is_rmb)
            add_value = self.parse_arg(formdata, 'add_value', rule=rules.is_rmb)
            time_length = self.parse_arg(formdata, 'time_length', rule=rules.is_number3)
            flow_length = self.parse_arg(formdata, 'flow_length', rule=rules.is_number3)
            operate_desc = self.parse_arg(formdata, 'operate_desc')
            account = self.db.query(models.TrAccount).get(account_number)
            if account.status not in (1, 4):
                raise ValueError(u'无效用户状态')
            node_id = self.db.query(models.TrCustomer.node_id).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.account_number == account_number).scalar()
            product = self.db.query(models.TrProduct).get(product_id)
            accept_log = models.TrAcceptLog()
            accept_log.id = utils.get_uuid()
            accept_log.accept_type = 'change'
            accept_log.accept_source = 'console'
            accept_log.account_number = account_number
            accept_log.accept_time = utils.get_currtime()
            accept_log.operator_name = self.operator.operator_name
            accept_log.accept_desc = u'用户资费变更为:%s;%s' % (product.product_name, utils.safeunicode(operate_desc))
            accept_log.stat_year = accept_log.accept_time[0:4]
            accept_log.stat_month = accept_log.accept_time[0:7]
            accept_log.stat_day = accept_log.accept_time[0:10]
            accept_log.sync_ver = tools.gen_sync_ver()
            self.db.add(accept_log)
            old_exoire_date = account.expire_date
            account.product_id = product.id
            if product.product_policy in (PPMonth,
             BOMonth,
             PPDay,
             BODay):
                account.expire_date = expire_date
                account.balance = 0
                account.time_length = 0
                account.flow_length = 0
            elif product.product_policy in (PPTimes, PPFlow):
                account.expire_date = MAX_EXPIRE_DATE
                account.balance = utils.yuan2fen(balance)
                account.time_length = 0
                account.flow_length = 0
            elif product.product_policy == BOTimes:
                account.expire_date = MAX_EXPIRE_DATE
                account.balance = 0
                account.time_length = utils.hour2sec(time_length)
                account.flow_length = 0
            elif product.product_policy == BOFlows:
                account.expire_date = MAX_EXPIRE_DATE
                account.balance = 0
                account.time_length = 0
                account.flow_length = utils.gb2kb(flow_length)
            account.sync_ver = tools.gen_sync_ver()
            order = models.TrCustomerOrder()
            order.order_id = utils.gen_order_id()
            order.customer_id = account.customer_id
            order.product_id = account.product_id
            order.account_number = account.account_number
            order.order_fee = 0
            order.actual_fee = utils.yuan2fen(add_value)
            order.pay_status = 1
            order.accept_id = accept_log.id
            order.order_source = 'console'
            order.create_time = utils.get_currtime()
            order.stat_year = order.create_time[0:4]
            order.stat_month = order.create_time[0:7]
            order.stat_day = order.create_time[0:10]
            order.order_desc = u'用户变更资费,变更前到期:%s,变更后到期:%s' % (old_exoire_date, account.expire_date)
            order.sync_ver = tools.gen_sync_ver()
            self.db.add(order)
            agency_id = self.db.query(models.TrCustomer.agency_id).filter_by(customer_id=account.customer_id).scalar()
            if agency_id and order.actual_fee > 0:
                agency = self.db.query(models.TrAgency).get(agency_id)
                if agency.amount < order.actual_fee:
                    raise ValueError(u'代理商预存款余额不足')
                agency_share = models.TrAgencyShare()
                agency_share.id = utils.get_uuid()
                agency_share.agency_id = agency_id
                agency_share.order_id = order.order_id
                agency_share.share_rate = agency.share_rate
                sfee = decimal.Decimal(order.actual_fee) * decimal.Decimal(agency.share_rate) / decimal.Decimal(100)
                sfee = int(sfee.to_integral_value())
                agency_share.share_fee = sfee
                agency_share.create_time = utils.get_currtime()
                agency_share.sync_ver = tools.gen_sync_ver()
                self.db.add(agency_share)
                agency.amount -= order.actual_fee
                agency.sync_ver = tools.gen_sync_ver()
                aorder = models.TrAgencyOrder()
                aorder.id = utils.get_uuid()
                aorder.agency_id = agency.id
                aorder.fee_type = 'cost'
                aorder.fee_value = -order.actual_fee
                aorder.fee_total = agency.amount
                aorder.fee_desc = u'用户 %s 资费变更扣费' % account_number
                aorder.create_time = agency_share.create_time
                aorder.sync_ver = tools.gen_sync_ver()
                self.db.add(aorder)
                agency.amount += agency_share.share_fee
                aorder2 = models.TrAgencyOrder()
                aorder2.id = utils.get_uuid()
                aorder2.agency_id = agency.id
                aorder2.fee_type = 'share'
                aorder2.fee_value = agency_share.share_fee
                aorder2.fee_total = agency.amount
                aorder2.fee_desc = u'用户 %s 变更资费分成(%s%%)' % (account_number, agency.share_rate)
                aorder2.create_time = agency_share.create_time
                aorder2.sync_ver = tools.gen_sync_ver()
                self.db.add(aorder2)
            self.add_oplog(accept_log.accept_desc)
            self.db.commit()
            dispatch.pub(redis_cache.CACHE_DELETE_EVENT, account_cache_key(account.account_number), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户资费变更失败:%s' % utils.safeunicode(err)
            logger.error(self.last_error, tag='account_change_error', username=formdata.get('account_number'))
            return False