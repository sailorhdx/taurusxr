#!/usr/bin/env python
# coding=utf-8
import decimal, os
decimal.getcontext().prec = 11
decimal.getcontext().rounding = decimal.ROUND_UP
FEES = PPMonth, PPTimes, BOMonth, BOTimes, PPFlow, BOFlows, PPMFlows, APMonth, PPDay, BODay = (0, 1, 2, 3, 4, 5, 7, 8, 9, 10)
ACCOUNT_STATUS = UsrPreAuth, UsrNormal, UsrPause, UsrCancel, UsrExpire, UsrPadding = (0, 1, 2, 3, 4, 5)
CARD_STATUS = CardInActive, CardActive, CardUsed, CardRecover = (0, 1, 2, 3)
CARD_TYPES = ProductCard, BalanceCard = (0, 1)
ORDER_STATUS = OUnPay, OPaid, OChecked = (0, 1, 2)
STAT_AUTH_ALL = 'STAT_AUTH_ALL'
STAT_AUTH_ACCEPT = 'STAT_AUTH_ACCEPT'
STAT_AUTH_REJECT = 'STAT_AUTH_REJECT'
STAT_AUTH_DROP = 'STAT_AUTH_DROP'
STAT_ACCT_ALL = 'STAT_ACCT_ALL'
STAT_ACCT_START = 'STAT_ACCT_START'
STAT_ACCT_UPDATE = 'STAT_ACCT_UPDATE'
STAT_ACCT_STOP = 'STAT_ACCT_STOP'
STAT_ACCT_ON = 'STAT_ACCT_ON'
STAT_ACCT_OFF = 'STAT_ACCT_OFF'
STAT_ACCT_DROP = 'STAT_ACCT_DROP'
STAT_ACCT_RETRY = 'STAT_ACCT_RETRY'
STATUS_TYPE_START = 1
STATUS_TYPE_STOP = 2
STATUS_TYPE_UPDATE = 3
STATUS_TYPE_UNLOCK = 4
STATUS_TYPE_CHECK_ONLINE = 5
STATUS_TYPE_ACCT_ON = 7
STATUS_TYPE_ACCT_OFF = 8
ACCEPT_TYPES = {'open': u'开户',
 'pause': u'停机',
 'resume': u'复机',
 'cancel': u'销户',
 'next': u'续费',
 'charge': u'充值',
 'change': u'变更',
 'auto_renew': u'自动续费',
 'apm_bill': u'后付费出账'}
TPL_TYPES = OpenNotify, NextNotify, ExpireNotify, IssuesNotify, VcodeNotify = ('open_notify', 'next_notify', 'expire_notify', 'issues_notify', 'vcode_notify')
ADMIN_MENUS = MenuSys, MenuNode, MenuRes, MenuUser, ResWlan, MenuAgency, MenuOpt, MenuStat = (u'系统管理', u'区域管理', u'资源管理', u'用户管理', u'无线认证', u'代理商管理', u'维护管理', u'查询统计')
MENU_ICONS = {u'系统管理': 'fa fa-cog',
 u'区域管理': 'fa fa-map-marker',
 u'资源管理': 'fa fa-desktop',
 u'用户管理': 'fa fa-users',
 u'无线认证': 'fa fa-signal',
 u'代理商管理': 'fa fa-user-md',
 u'维护管理': 'fa fa-wrench',
 u'查询统计': 'fa fa-bar-chart'}
MAX_EXPIRE_DATE = '3000-12-30'
param_cache_key = 'toughradius.cache.param.{0}'.format
tplid_cache_key = 'toughradius.cache.sms.tplid.{0}'.format
wlanattr_cache_key = 'toughradius.cache.wlan.domain.attr.{0}'.format
account_cache_key = 'toughradius.cache.account.{0}'.format
account_attr_cache_key = 'toughradius.cache.account.attr.{0}.{1}'.format
product_cache_key = 'toughradius.cache.product.{0}'.format
product_attrs_cache_key = 'toughradius.cache.product.attrs.{0}'.format
bas_cache_key = 'toughradius.cache.bas.{0}'.format
bas_cache_ipkey = 'toughradius.cache.bas.ip.{0}'.format
bas_attr_cache_key = 'toughradius.cache.bas.attr.{0}.{1}'.format
account_bind_basip_key = 'toughradius.account.bind.bas.ipaddr.{0}'.format
account_bind_basid_key = 'toughradius.account.bind.bas.nasid.{0}'.format
radius_statcache_key = 'toughradius.cache.radius.stat'
online_statcache_key = 'toughradius.cache.online.stat'
flow_statcache_key = 'toughradius.cache.flow.stat'
order_paycaache_key = 'toughradius.cache.order.pay.{0}'.format
order_wxpaycaache_key = 'toughradius.cache.order.wxpay.{0}'.format
toughcloud_ping_key = 'toughradius.cache.toughcloud.ping'
hadb_sync_status_cache_key = 'toughradius.cache.hadb.status'
hadb_sync_count_cache_key = 'toughradius.cache.hadb.count'
wlanportal_cache_key = 'toughradius.cache.wlanportal.ac.{0}'.format
wlan_domain_cache_key = 'toughradius.cache.wlanportal.domain.{0}'.format
wlan_template_cache_key = 'toughradius.cache.wlanportal.template.{0}'.format
DEFAULT_RDB = 0
LOGTRACE_RDB = 1
SSPORTAL_RDB = 2
