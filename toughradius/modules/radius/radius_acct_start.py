#!/usr/bin/env python
# coding=utf-8
from toughradius.modules.radius.radius_basic import RadiusBasic
from toughradius.modules.radius.radius_billing import RadiusBilling
from toughradius.modules.events.settings import UNLOCK_ONLINE_EVENT
from toughradius.toughlib.storage import Storage
from toughradius.modules import models
from toughradius.toughlib import utils, dispatch, logger
from toughradius.modules.settings import *
import datetime

class RadiusAcctStart(RadiusBilling):

    def __init__(self, dbengine = None, cache = None, aes = None, request = None):
        RadiusBilling.__init__(self, dbengine, cache, aes, request)

    def acctounting(self):
        if self.is_online(self.request.nas_addr, self.request.acct_session_id):
            return logger.error(u'用户:%s 已经在线' % self.request.acct_session_id, tag='radius_acct_start_error')
        if not self.account:
            dispatch.pub(UNLOCK_ONLINE_EVENT, self.request.account_number, self.request.nas_addr, self.request.acct_session_id, async=True)
            return logger.error(u'用户:%s 不存在' % self.request.account_number, tag='radius_acct_start_error')
        online = Storage(account_number=self.request.account_number, nas_addr=self.request.nas_addr, acct_session_id=self.request.acct_session_id, acct_start_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), framed_ipaddr=self.request.framed_ipaddr, mac_addr=self.request.mac_addr or '', nas_port_id=self.request.nas_port_id, billing_times=0, input_total=0, output_total=0, start_source=STATUS_TYPE_START)
        self.add_online(online)
        logger.info(u'用户:%s 记账开始, 新增在线用户数据' % online.account_number, trace='radius', username=online.account_number)