#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils, dispatch
from toughradius.toughlib import logger
from toughradius.modules import models
from toughradius.modules.events.event_basic import BasicEvent
from toughradius.modules.settings import IssuesNotify
from toughradius.modules.events.settings import EVENT_SENDSMS, EVENT_SEND_WECHAT

class IssuesNotifyEvent(BasicEvent):

    def event_issues_assign(self, account_number, builder_phone = None, wechat_oid = None, content = None):
        userinfo = self.get_customer_info(account_number)
        if wechat_oid:
            content = u'你有新的工单要处理：\n\n用户账号(姓名)：{0}({1})\n联系电话：{2}\n地址：{3}\n工单描述：{4}\n'.format(account_number, userinfo.realname, userinfo.mobile, userinfo.install_address, content)
            dispatch.pub(EVENT_SEND_WECHAT, wechat_oid, utils.safeunicode(content))
        tplid = self.get_tpl_id(IssuesNotify)
        if not tplid:
            return
        args = [utils.safestr(userinfo.realname),
         utils.safestr(userinfo.install_address),
         userinfo.mobile,
         utils.safestr(content)]
        kwargs = {}
        kwargs['customer'] = utils.safestr(userinfo.realname)
        kwargs['address'] = utils.safestr(userinfo.install_address)
        kwargs['mobile'] = userinfo.mobile
        kwargs['content'] = utils.safestr(content)
        dispatch.pub(EVENT_SENDSMS, builder_phone, tplid, args=args, kwargs=kwargs)


def __call__(dbengine = None, mcache = None, **kwargs):
    return IssuesNotifyEvent(dbengine=dbengine, mcache=mcache, **kwargs)