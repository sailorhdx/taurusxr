#!/usr/bin/env python
# coding=utf-8
import datetime
import decimal
import traceback
from toughradius.toughlib import utils, logger, dispatch
from toughradius.modules import models
from toughradius.modules.settings import *
from toughradius.modules.radius.radius_basic import RadiusBasic
from toughradius.modules.events.settings import UNLOCK_ONLINE_EVENT
from toughradius.modules.events.settings import CHECK_ONLINE_EVENT

class RadiusAuth(RadiusBasic):

    def __init__(self, dbengine = None, cache = None, aes = None, request = None):
        RadiusBasic.__init__(self, dbengine, cache, aes, request)
        self.reply = {'code': 0,
         'msg': 'success',
         'attrs': {}}
        self.filters = [self.status_filter,
         self.bind_filter,
         self.policy_filter,
         self.limit_filter,
         self.session_filter,
         self.set_radius_attr,
         self.start_billing]

    def failure(self, msg):
        self.reply = {}
        self.reply['code'] = 1
        self.reply['msg'] = msg
        return False

    def authorize(self):
        try:
            if not self.account:
                self.failure(u'用户:%s 不存在' % self.request.account_number)
                return self.reply
            self.product = self.get_product_by_id(self.account.product_id)
            if not self.product:
                self.failure(u'用户:%s 认证时，产品套餐 id=%s 不存在' % (self.request.account_number, self.account.product_id))
                return self.reply
            for filter_func in self.filters:
                if not filter_func():
                    return self.reply

            return self.reply
        except Exception as err:
            self.failure(u'用户:%s 认证失败, %s' % (self.request.account_number, utils.safeunicode(err.message)))
            logger.exception(err, tag='radius_auth_error')
            return self.reply

    def check_free_auth(self, errmsg = ''):
        """ 用户免授权检查：如果用户订购资费支持到期免授权，则下发默认会话时长和资费设定的最大限速。
        """
        expire_ipaddr_pool = self.get_param_value('expire_ipaddr_pool')
        if expire_ipaddr_pool not in ('none', '', None):
            self.reply['input_rate'] = self.product.free_auth_uprate
            self.reply['output_rate'] = self.product.free_auth_downrate
            self.reply['attrs']['Framed-Pool'] = expire_ipaddr_pool
            self.reply['attrs']['Session-Timeout'] = int(self.get_param_value('radius_max_session_timeout', 86400))
            return True
        elif self.product.free_auth == 0:
            return self.failure(u'用户:%s 授权已过期, %s' % (self.request.account_number, errmsg))
        else:
            self.reply['input_rate'] = self.product.free_auth_uprate
            self.reply['output_rate'] = self.product.free_auth_downrate
            self.reply['attrs']['Session-Timeout'] = int(self.get_param_value('radius_max_session_timeout', 86400))
            return True
            return None

    def start_billing(self):
        if self.account.status == UsrPreAuth:
            _now = datetime.datetime.now()
            old_start = datetime.datetime.strptime(self.account.create_time, '%Y-%m-%d %H:%M:%S')
            old_end = datetime.datetime.strptime(self.account.expire_date, '%Y-%m-%d')
            day_len = old_end - old_start
            new_expire = (_now + day_len).strftime('%Y-%m-%d')
            self.update_user_expire(new_expire)
            logger.info(u'user:%s 账号未激活状态更新为正常，开始计费' % self.request.account_number, trace='radius', username=self.request.account_number)

    def status_filter(self):
        """ 1：用户过期，状态,密码检查 """
        self.reply['username'] = self.request.account_number
        is_pwdok = self.request.radreq.is_valid_pwd(self.aes.decrypt(self.account.password))
        self.reply['attrs'].update(self.request.radreq.resp_attrs)
        if self.request.bypass == 1 and not is_pwdok:
            return self.failure(u'用户:%s 密码错误' % self.request.account_number)
        if self.account.status == UsrExpire:
            return self.check_free_auth()
        if self.account.status in (UsrPause, UsrCancel, UsrPadding):
            return self.failure(u'用户:%s 状态:%s 无效' % (self.request.account_number, self.account.status))
        return True

    def bind_filter(self):
        """ 2：用户mac，vlan绑定关系检查 """
        macaddr = self.request['macaddr']
        if macaddr and self.account.mac_addr:
            if self.account.bind_mac == 1 and macaddr not in self.account.mac_addr:
                return self.failure(u'user:%s 绑定网卡地址不正确' % self.request.account_number)
        elif macaddr and not self.account.mac_addr:
            self.update_user_mac(macaddr)
        vlan_id1 = int(self.request['vlanid1'])
        vlan_id2 = int(self.request['vlanid2'])
        if vlan_id1 > 0 and self.account.vlan_id1 > 0:
            if self.account.bind_vlan == 1 and vlan_id1 != self.account.vlan_id1:
                return self.failure(u'用户:%s vlanid1 绑定不正确' % self.request.account_number)
        elif vlan_id1 > 0 and self.account.vlan_id1 == 0:
            self.update_user_vlan_id1(vlan_id1)
        if vlan_id2 > 0 and self.account.vlan_id2 > 0:
            if self.account.bind_vlan == 1 and vlan_id2 != self.account.vlan_id2:
                return self.failure(u'用户:%s vlanid2 绑定不正确' % self.request.account_number)
        elif vlan_id2 > 0 and self.account.vlan_id2 == 0:
            self.update_user_vlan_id2(vlan_id2)
        return True

    def policy_filter(self):
        """ 3：用户资费策略检查 """
        acct_policy = self.product.product_policy or PPMonth
        input_max_limit = self.product.input_max_limit
        output_max_limit = self.product.output_max_limit
        if utils.is_expire(self.account.expire_date):
            return self.check_free_auth()
        if acct_policy == BOTimes:
            if self.get_user_time_length() <= 0:
                return self.check_free_auth(u'用户剩余时长不足')
        elif acct_policy in (BOFlows, PPMFlows):
            if self.get_user_flow_length() <= 0 and self.get_user_fixd_flow_length() <= 0:
                return self.check_free_auth(u'用户剩余流量不足')
        self.reply['input_rate'] = input_max_limit
        self.reply['output_rate'] = output_max_limit
        return True

    def limit_filter(self):
        """ 4：用户并发数控制检查 """
        online_count = self.count_online()
        if self.account.user_concur_number == 0:
            return True
        if self.account.user_concur_number > 0:
            try:
                if online_count == self.account.user_concur_number:
                    auto_unlock = int(self.get_param_value('radius_auth_auto_unlock', 0)) == 1
                    online = self.get_first_online(self.request.account_number)
                    if not auto_unlock:
                        dispatch.pub(CHECK_ONLINE_EVENT, online.account_number, async=True)
                        return self.failure(u'用户:%s 在线数超过限制' % self.request.account_number)
                    else:
                        dispatch.pub(UNLOCK_ONLINE_EVENT, online.account_number, online.nas_addr, online.acct_session_id, async=True)
                        return True
            except Exception as err:
                raise Exception(u'用户:%s 在线数超过限制，自动解锁错误: %s' % (self.request.account_number, utils.safeunicode(traceback.format_exc())))

        if online_count > self.account.user_concur_number:
            return self.failure(u'用户:%s 在线数超过限制' % self.request.account_number)
        return True

    def session_filter(self):
        """ 5：用户会话时长计算 """
        session_timeout = int(self.get_param_value('radius_max_session_timeout', 86400))
        acct_interim_intelval = int(self.get_param_value('radius_acct_interim_intelval', 0))
        if acct_interim_intelval > 0:
            self.reply['attrs']['Acct-Interim-Interval'] = acct_interim_intelval
        acct_policy = self.product.product_policy or PPMonth

        def _calc_session_timeout(acct_policy):
            if acct_policy in (PPMonth, BOMonth):
                expire_date = self.account.expire_date
                _datetime = datetime.datetime.now()
                _expire_datetime = datetime.datetime.strptime(expire_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
                _sec = (_expire_datetime - _datetime).total_seconds()
                _sec = session_timeout if _sec < 0 else _sec
                if _sec < session_timeout:
                    return _sec
                return session_timeout
            if acct_policy == BOTimes:
                _session_timeout = self.account.time_length
                if _session_timeout < session_timeout:
                    return _session_timeout
                return session_timeout
            else:
                return session_timeout

        self.reply['attrs']['Session-Timeout'] = int(_calc_session_timeout(acct_policy))
        return True

    def set_radius_attr(self):
        for attr in self.get_product_attrs(self.account.product_id, radius=True) or []:
            self.reply['attrs'].setdefault(attr.attr_name, []).append(attr.attr_value)

        if self.account.ip_address:
            self.reply['attrs']['Framed-IP-Address'] = self.account.ip_address
        rate_code_attr = self.get_product_attr(self.account.product_id, 'limit_rate_code')
        if rate_code_attr:
            self.reply['rate_code'] = rate_code_attr.attr_value
        self.reply['domain'] = self.account.domain
        return True