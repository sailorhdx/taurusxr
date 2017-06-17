#!/usr/bin/env python
# coding=utf-8
import traceback
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

class AccountCharge(BaseService):

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
        if vcard.card_type not in ('balance', 'flowlen', 'timelen'):
            self.last_error = u'充值卡不支持充值'
            return False
        if self.aes.decrypt(vcard.card_pwd) != vcard_pwd:
            self.last_error = u'充值卡密码错误'
            return False
        if vcard.card_type == 'balance' and product.product_policy not in (PPFlow, PPTimes):
            self.last_error = u'当前资费不支持余额卡'
            return False
        if vcard.card_type == 'flowlen' and product.product_policy not in (BOFlows,):
            self.last_error = u'当前资费不支持流量卡'
            return False
        if vcard.card_type == 'timelen' and product.product_policy not in (BOTimes,):
            self.last_error = u'当前资费不支持时长卡'
            return False
        return True

    @logparams
    def charge(self, formdata, **kwargs):
        """用户充值，预付费时长，预付费流量有效

        :param formdata:   用户充值参数表
        :type formdata:    dict
        
        formdata params:

        :param account_number:   用户账号
        :type account_number:    string
        :param operate_desc:    操作描述
        :type operate_desc:     string
        :param fee_value:    费用金额(元) x.xx
        :type fee_value:     string
        :param order_id:    订单号(可选) 16-32位字符串
        :type order_id:     string
        """
        try:
            account_number = self.parse_arg(formdata, 'account_number', rule=rules.not_null)
            fee_value = self.parse_arg(formdata, 'fee_value', rule=rules.is_rmb)
            operate_desc = self.parse_arg(formdata, 'operate_desc', defval='')
            order_id = self.parse_arg(formdata, 'order_id', defval=utils.gen_order_id(), rule=rules.not_null)
            vcard_code = self.parse_arg(formdata, 'vcard_code', defval='')
            vcard_pwd = self.parse_arg(formdata, 'vcard_pwd', defval='')
            account = self.db.query(models.TrAccount).get(account_number)
            if account.status in (3, 4, 5):
                raise ValueError(u'无效用户状态')
            node_id = self.db.query(models.TrCustomer.node_id).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.account_number == account_number).scalar()
            charge_timelen = 0
            charge_flowlen = 0
            product = self.db.query(models.TrProduct).get(account.product_id)
            vcard = None
            if vcard_code and vcard_pwd:
                vcard = self.db.query(models.TrValCard).get(vcard_code)
                if not self.check_vcard(vcard, vcard_pwd, product):
                    return False
                if vcard.card_type == 'balance':
                    fee_value = vcard.credit
                if vcard.card_type == 'flowlen':
                    fee_value = vcard.fee_price
                    charge_flowlen = utils.gb2kb(vcard.flowlen)
                if vcard.card_type == 'timelen':
                    fee_value = vcard.fee_price
                    charge_timelen = utils.hour2sec(vcard.timelen)
            accept_log = models.TrAcceptLog()
            accept_log.id = utils.get_uuid()
            accept_log.accept_type = 'charge'
            accept_log.accept_source = 'console'
            _new_fee = account.balance + utils.yuan2fen(fee_value)
            accept_log.accept_desc = operate_desc
            accept_log.account_number = account_number
            accept_log.accept_time = utils.get_currtime()
            accept_log.operator_name = self.operator.operator_name
            accept_log.stat_year = accept_log.accept_time[0:4]
            accept_log.stat_month = accept_log.accept_time[0:7]
            accept_log.stat_day = accept_log.accept_time[0:10]
            accept_log.sync_ver = tools.gen_sync_ver()
            self.db.add(accept_log)
            order = models.TrCustomerOrder()
            order.id = utils.get_uuid()
            order.order_id = order_id
            order.customer_id = account.customer_id
            order.product_id = product.id
            order.account_number = account_number
            order.order_fee = utils.yuan2fen(fee_value)
            order.actual_fee = utils.yuan2fen(fee_value)
            order.pay_status = 1
            order.accept_id = accept_log.id
            order.order_source = 'console'
            order.create_time = utils.get_currtime()
            order.order_desc = accept_log.accept_desc or ''
            order.stat_year = order.create_time[0:4]
            order.stat_month = order.create_time[0:7]
            order.stat_day = order.create_time[0:10]
            order.sync_ver = tools.gen_sync_ver()
            if vcard:
                vcard.status = 2
                vcard.use_time = utils.get_currtime()
                vcard.customer_id = account.customer_id
            _old_balance = account.balance
            _old_flowlen = account.flow_length
            _old_timelen = account.time_length
            if not vcard or vcard.card_type not in ('timelen', 'flowlen'):
                account.balance += order.actual_fee
            account.flow_length += charge_flowlen
            account.time_length += charge_timelen
            order.order_desc += u' 充值前余额%s元,充值后余额%s元；' % (utils.fen2yuan(_old_balance), utils.fen2yuan(account.balance))
            order.order_desc += u'充值前流量%sG,充值后流量%sG;' % (utils.kb2gb(_old_flowlen), utils.kb2gb(account.flow_length))
            order.order_desc += u'充值前时长%s小时,充值后时长%s小时;' % (utils.sec2hour(_old_timelen), utils.sec2hour(account.time_length))
            self.db.add(order)
            self.add_oplog(order.order_desc)
            self.db.commit()
            dispatch.pub(ACCOUNT_NEXT_EVENT, order.account_number, async=True)
            dispatch.pub(redis_cache.CACHE_DELETE_EVENT, account_cache_key(account.account_number), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户充值失败:%s' % utils.safeunicode(err)
            logger.error(self.last_error, tag='account_charge_error', username=formdata.get('account_number'))
            traceback.print_exc()
            return False

        return