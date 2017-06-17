#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils, dispatch
from toughradius.modules.events.event_basic import BasicEvent
from toughradius.modules.settings import ExpireNotify, OpenNotify, NextNotify
from toughradius.modules.events.settings import EVENT_SENDSMS, EVENT_SENDMAIL, EVENT_SEND_WECHAT

class AccountNotifyEvent(BasicEvent):

    def event_wechat_account_open(self, account_number):
        """客户账号开户微信通知
        """
        userinfo = self.get_customer_info(account_number)
        content_tpl = self.get_content_template(OpenNotify)
        if not content_tpl:
            return
        content = content_tpl.replace('{customer_name}', utils.safeunicode(userinfo.realname))
        content = content.replace('{product_name}', utils.safeunicode(userinfo.product_name))
        content = content.replace('{username}', account_number)
        content = content.replace('{expire_date}', userinfo.expire_date)
        dispatch.pub(EVENT_SEND_WECHAT, userinfo.wechat_oid, utils.safeunicode(content))

    def event_wechat_account_expire(self, account_number):
        """客户账号到期微信通知
        """
        userinfo = self.get_customer_info(account_number)
        content_tpl = self.get_content_template(ExpireNotify)
        if not content_tpl:
            return
        content = content_tpl.replace('{customer_name}', utils.safeunicode(userinfo.realname))
        content = content.replace('{product_name}', utils.safeunicode(userinfo.product_name))
        content = content.replace('{username}', account_number)
        content = content.replace('{expire_date}', userinfo.expire_date)
        dispatch.pub(EVENT_SEND_WECHAT, userinfo.wechat_oid, utils.safeunicode(content))

    def event_wechat_account_next(self, account_number):
        """客户账号续费微信通知
        """
        userinfo = self.get_customer_info(account_number)
        content_tpl = self.get_content_template(NextNotify)
        if not content_tpl:
            return
        content = content_tpl.replace('{customer_name}', utils.safeunicode(userinfo.realname))
        content = content.replace('{product_name}', utils.safeunicode(userinfo.product_name))
        content = content.replace('{username}', account_number)
        content = content.replace('{expire_date}', userinfo.expire_date)
        dispatch.pub(EVENT_SEND_WECHAT, userinfo.wechat_oid, utils.safeunicode(content))

    def event_sms_account_open(self, account_number):
        userinfo = self.get_customer_info(account_number)
        tplid = self.get_tpl_id(OpenNotify)
        if not tplid:
            return
        args = [utils.safestr(userinfo.realname),
         account_number,
         utils.safestr(userinfo.product_name),
         userinfo.expire_date]
        kwargs = {}
        kwargs['customer'] = utils.safestr(userinfo.realname)
        kwargs['username'] = account_number
        kwargs['product'] = utils.safestr(userinfo.product_name)
        kwargs['expire'] = userinfo.expire_date
        dispatch.pub(EVENT_SENDSMS, userinfo.mobile, tplid, args=args, kwargs=kwargs)

    def event_sms_account_next(self, account_number):
        userinfo = self.get_customer_info(account_number)
        tplid = self.get_tpl_id(NextNotify)
        if not tplid:
            return
        args = [utils.safestr(userinfo.realname),
         account_number,
         utils.safestr(userinfo.product_name),
         userinfo.expire_date]
        kwargs = {}
        kwargs['customer'] = utils.safestr(userinfo.realname)
        kwargs['username'] = account_number
        kwargs['product'] = utils.safestr(userinfo.product_name)
        kwargs['expire'] = userinfo.expire_date
        dispatch.pub(EVENT_SENDSMS, userinfo.mobile, tplid, args=args, kwargs=kwargs)

    def event_sms_account_expire(self, account_number):
        userinfo = self.get_customer_info(account_number)
        tplid = self.get_tpl_id(ExpireNotify)
        if not tplid:
            return
        args = [utils.safestr(userinfo.realname),
         account_number,
         utils.safestr(userinfo.product_name),
         userinfo.expire_date]
        kwargs = {}
        kwargs['customer'] = utils.safestr(userinfo.realname)
        kwargs['username'] = account_number
        kwargs['product'] = utils.safestr(userinfo.product_name)
        kwargs['expire'] = userinfo.expire_date
        dispatch.pub(EVENT_SENDSMS, userinfo.mobile, tplid, args=args, kwargs=kwargs)

    def event_mail_account_open(self, account_number):
        userinfo = self.get_customer_info(account_number)
        content_tpl = self.get_content_template(OpenNotify)
        if not content_tpl:
            return
        content = content_tpl.replace('{customer_name}', utils.safeunicode(userinfo.realname))
        content = content.replace('{product_name}', utils.safeunicode(userinfo.product_name))
        content = content.replace('{username}', account_number)
        content = content.replace('{expire_date}', userinfo.expire_date)
        dispatch.pub(EVENT_SENDMAIL, userinfo.email, u'用户开户通知邮件', utils.safeunicode(content))

    def event_mail_account_next(self, account_number):
        userinfo = self.get_customer_info(account_number)
        content_tpl = self.get_content_template(NextNotify)
        if not content_tpl:
            return
        content = content_tpl.replace('{customer_name}', utils.safeunicode(userinfo.realname))
        content = content.replace('{product_name}', utils.safeunicode(userinfo.product_name))
        content = content.replace('{username}', account_number)
        content = content.replace('{expire_date}', userinfo.expire_date)
        dispatch.pub(EVENT_SENDMAIL, userinfo.email, u'用户续费通知邮件', utils.safeunicode(content))

    def event_mail_account_expire(self, account_number):
        userinfo = self.get_customer_info(account_number)
        content_tpl = self.get_content_template(ExpireNotify)
        if not content_tpl:
            return
        content = content_tpl.replace('{customer_name}', utils.safeunicode(userinfo.realname))
        content = content.replace('{product_name}', utils.safeunicode(userinfo.product_name))
        content = content.replace('{username}', account_number)
        content = content.replace('{expire_date}', userinfo.expire_date)
        dispatch.pub(EVENT_SENDMAIL, userinfo.email, u'用户到期通知邮件', utils.safeunicode(content))


def __call__(dbengine = None, mcache = None, **kwargs):
    return AccountNotifyEvent(dbengine=dbengine, mcache=mcache, **kwargs)