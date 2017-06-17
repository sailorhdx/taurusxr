#!/usr/bin/env python
# coding=utf-8
from toughradius.modules.settings import *
from hashlib import md5
from toughradius.modules import models
from toughradius.toughlib import utils, dispatch, redis_cache, logger
from toughradius.modules.events.settings import ACCOUNT_NEXT_EVENT
from toughradius.modules.events.settings import UNLOCK_ONLINE_EVENT
from toughradius.modules.dbservice import BaseService
from toughradius.modules.dbservice import logparams
from toughradius.common import tools
from toughradius.toughlib.btforms import rules
from toughradius.modules.events import settings as evset

class AccountRenew(BaseService):

    def check_vcard(self, vcard, vcard_pwd, product):
        if not vcard:
            self.last_error = u'充值卡不存在'
            return False
        if vcard.status == 0:
            self.last_error = u'充值卡未激活'
            return False
        if vcard.status == 2:
            self.last_error = u'充值卡已使用'
            return False
        if utils.is_expire(vcard.expire_date):
            self.last_error = u'充值卡已过期'
            return False
        if vcard.card_type not in 'product':
            self.last_error = u'充值卡不是套餐卡'
            return False
        if self.aes.decrypt(vcard.card_pwd) != vcard_pwd:
            self.last_error = u'充值卡密码错误'
            return False
        if product.product_policy not in (BOMonth, BOFlows, BOTimes):
            self.last_error = u'当前资费不支持此充值卡'
            return False
        pattr = self.db.query(models.TrProductAttr).filter_by(product_id=product.id, attr_name='product_tag', attr_value=vcard.product_tag).first()
        if not pattr:
            self.last_error = u'当前资费不支持此充值卡'
            return False
        return True

    @logparams
    def renew(self, formdata, **kwargs):
        """用户续费

        :param formdata:   用户续费参数表
        :type formdata:    dict
        
        formdata params:
        
        :param account_number:   用户账号
        :type account_number:    string
        :param operate_desc:    操作描述
        :type operate_desc:     string
        :param fee_value:    费用金额(元) x.xx
        :type fee_value:     string
        :param months:    订购月数，预付费包月有效
        :type months:     int
        :param giftdays:    赠送天数
        :type giftdays:     int
        :param expire_date:    到期时间 yyyy-mm-dd
        :type expire_date:     string
        :param order_id:    订单号(可选) 16-32位字符串
        :type order_id:     string
        """
        try:
            account_number = self.parse_arg(formdata, 'account_number', rule=rules.not_null)
            product_id = self.parse_arg(formdata, 'product_id', rule=rules.not_null)
            operate_desc = self.parse_arg(formdata, 'operate_desc', defval='')
            fee_value = self.parse_arg(formdata, 'fee_value', rule=rules.is_rmb)
            months = self.parse_arg(formdata, 'months', defval='0', rule=rules.is_number)
            days = self.parse_arg(formdata, 'days', defval='0', rule=rules.is_number)
            giftdays = self.parse_arg(formdata, 'giftdays', defval='0', rule=rules.is_number)
            expire_date = self.parse_arg(formdata, 'expire_date', rule=rules.is_date)
            order_id = self.parse_arg(formdata, 'order_id', defval=utils.gen_order_id(), rule=rules.not_null)
            vcard_code = self.parse_arg(formdata, 'vcard_code', defval='')
            vcard_pwd = self.parse_arg(formdata, 'vcard_pwd', defval='')
            account = self.db.query(models.TrAccount).get(account_number)
            if account.status in (3, 4, 5):
                raise ValueError(u'无效用户状态')
            node_id = self.db.query(models.TrCustomer.node_id).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.account_number == account_number).scalar()
            product = self.db.query(models.TrProduct).get(account.product_id)
            vcard = None
            if vcard_code and vcard_pwd:
                vcard = self.db.query(models.TrValCard).get(vcard_code)
                if not self.check_vcard(vcard, vcard_pwd, product):
                    return False
            accept_log = models.TrAcceptLog()
            accept_log.id = utils.get_uuid()
            accept_log.accept_type = 'next'
            accept_log.accept_source = 'console'
            accept_log.accept_desc = u'用户续费：上网账号:%s，续费%s元;%s' % (account_number, fee_value, utils.safeunicode(operate_desc))
            accept_log.account_number = account_number
            accept_log.accept_time = utils.get_currtime()
            accept_log.operator_name = self.operator.operator_name
            accept_log.stat_year = accept_log.accept_time[0:4]
            accept_log.stat_month = accept_log.accept_time[0:7]
            accept_log.stat_day = accept_log.accept_time[0:10]
            accept_log.sync_ver = tools.gen_sync_ver()
            self.db.add(accept_log)
            order_fee = 0
            if product.product_policy == PPMonth:
                order_fee = decimal.Decimal(product.fee_price) * decimal.Decimal(months)
                order_fee = int(order_fee.to_integral_value())
            if product.product_policy == PPDay:
                order_fee = decimal.Decimal(product.fee_price) * decimal.Decimal(days)
                order_fee = int(order_fee.to_integral_value())
            elif product.product_policy in (BOMonth,
             BOTimes,
             BOFlows,
             BODay):
                order_fee = int(product.fee_price)
            order = models.TrCustomerOrder()
            order.id = utils.get_uuid()
            order.order_id = order_id
            order.customer_id = account.customer_id
            order.product_id = product_id
            order.account_number = account_number
            order.order_fee = order_fee
            order.actual_fee = utils.yuan2fen(fee_value)
            order.pay_status = 1
            order.accept_id = accept_log.id
            order.order_source = 'console'
            order.create_time = utils.get_currtime()
            order.stat_year = order.create_time[0:4]
            order.stat_month = order.create_time[0:7]
            order.stat_day = order.create_time[0:10]
            order.sync_ver = tools.gen_sync_ver()
            if vcard:
                vcard.status = 2
                vcard.use_time = utils.get_currtime()
                vcard.customer_id = account.customer_id
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
                aorder = models.TrAgencyOrder()
                aorder.id = utils.get_uuid()
                aorder.agency_id = agency.id
                aorder.fee_type = 'cost'
                aorder.fee_value = -order.actual_fee
                aorder.fee_total = agency.amount
                aorder.fee_desc = u'用户 %s 续费扣费' % account_number
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
                aorder2.fee_desc = u'用户 %s 续费分成(%s%%)' % (account_number, agency.share_rate)
                aorder2.create_time = agency_share.create_time
                aorder2.sync_ver = tools.gen_sync_ver()
                self.db.add(aorder2)
            if product_id != account.product_id:
                account.product_id = product_id
            old_expire_date = account.expire_date
            if account.status != UsrPreAuth:
                account.status = 1
            account.expire_date = expire_date
            if product.product_policy == BOTimes:
                account.time_length += product.fee_times
            elif product.product_policy == BOFlows:
                account.flow_length += product.fee_flows
            account.sync_ver = tools.gen_sync_ver()
            order.order_desc = u'用户续费,续费前到期:%s,续费后到期:%s, 赠送天数: %s' % (old_expire_date, account.expire_date, giftdays)
            self.db.add(order)
            self.add_oplog(order.order_desc)
            self.db.commit()
            dispatch.pub(ACCOUNT_NEXT_EVENT, order.account_number, async=True)
            dispatch.pub(redis_cache.CACHE_DELETE_EVENT, account_cache_key(account.account_number), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户续费失败:%s' % utils.safeunicode(err)
            logger.error(self.last_error, tag='account_renew_error', username=formdata.get('account_number'))
            return False

        return