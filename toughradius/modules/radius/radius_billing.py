#!/usr/bin/env python
# coding=utf-8
import datetime
from toughradius.modules.radius.radius_basic import RadiusBasic
from toughradius.modules.events.settings import UNLOCK_ONLINE_EVENT
from toughradius.toughlib.storage import Storage
from toughradius.modules import models
from toughradius.toughlib import utils, logger, dispatch
from toughradius.modules.settings import *
from toughradius.toughlib.utils import timecast
import decimal
decimal.getcontext().prec = 16
decimal.getcontext().rounding = decimal.ROUND_UP

class RadiusBilling(RadiusBasic):

    def __init__(self, dbengine = None, cache = None, aes = None, request = None):
        RadiusBasic.__init__(self, dbengine, cache, aes, request)
        self.bill_funcs = {BOTimes: self.bill_botimes,
         BOFlows: self.bill_boflows}

    def billing(self, online):
        product = self.get_product_by_id(self.account.product_id)
        if not product:
            lmsg = 'product <%s> not exists' % self.account.product_id
            logger.error(lmsg)
            return
        if product.product_policy not in (PPTimes,
         BOTimes,
         PPFlow,
         BOFlows,
         PPMFlows):
            self.update_online(self.request.nas_addr, self.request.acct_session_id, billing_times=self.request.acct_session_time, input_total=self.get_input_total(), output_total=self.get_output_total())
        else:
            try:
                self.bill_funcs[product.product_policy](online, product)
            except Exception as err:
                logger.exception(err, tag='radius_acct_billing_error')

    def bill_botimes(self, online, product):
        logger.info('%s > Buyout long time billing ' % self.account.account_number)
        time_length = self.get_user_time_length()
        sessiontime = self.request.acct_session_time
        billing_times = online.billing_times
        acct_times = sessiontime - billing_times
        #logger.info('%s bill_botimes > time_length: %s, sessiontime: %s, billing_times: %s,  acct_times: %s' % (self.account.account_number, time_length, sessiontime, billing_times, acct_times))
        if acct_times < 0:
            acct_times = 0
        user_time_length = time_length - acct_times
        #logger.info('%s bill_botimes > time_length: %s, sessiontime: %s, billing_times: %s,  acct_times: %s' % (self.account.account_number, time_length, sessiontime, billing_times, acct_times))
        #logger.info('%s bill_botimes > user_time_length(%s) = time_length(%s) - acct_times(%s)' % (self.account.account_number, user_time_length, time_length, acct_times))
        if user_time_length < 0:
            user_time_length = 0
        self.update_billing(Storage(account_number=online.account_number, nas_addr=online.nas_addr, acct_session_id=online.acct_session_id, acct_start_time=online.acct_start_time, acct_session_time=self.request.acct_session_time, input_total=self.get_input_total(), output_total=self.get_output_total(), acct_times=acct_times, acct_flows=0, acct_fee=0, actual_fee=0, balance=0, time_length=user_time_length, flow_length=0, is_deduct=1, create_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        if user_time_length == 0 and product.free_auth == 0:
            dispatch.pub(UNLOCK_ONLINE_EVENT, online.account_number, online.nas_addr, online.acct_session_id, async=True)

    def bill_boflows(self, online, product):#u'买断流量'
        logger.info('%s > Buyout flow billing ' % self.account.account_number)
        flow_length = self.get_user_flow_length()
        output_total = self.get_output_total()
        billing_output_total = online.output_total
        acct_flows = output_total - billing_output_total
        if acct_flows < 0:
            acct_flows = 0
        user_flow_length = flow_length - acct_flows
        if user_flow_length < 0:
            user_flow_length = 0
        self.update_billing(Storage(account_number=online.account_number, nas_addr=online.nas_addr, acct_session_id=online.acct_session_id, acct_start_time=online.acct_start_time, acct_session_time=self.request.acct_session_time, input_total=self.get_input_total(), output_total=self.get_output_total(), acct_times=0, acct_flows=acct_flows, acct_fee=0, actual_fee=0, balance=0, time_length=0, flow_length=user_flow_length, is_deduct=1, create_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        if user_flow_length == 0 and product.free_auth == 0:
            dispatch.pub(UNLOCK_ONLINE_EVENT, online.account_number, online.nas_addr, online.acct_session_id, async=True)
