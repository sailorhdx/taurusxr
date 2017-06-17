#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.toughlib import logger
from toughradius.toughlib import utils
from toughradius.toughlib import dispatch
from toughradius.toughlib.permit import permit
from toughradius.modules.mps.base import BaseHandler
from twisted.internet import defer
from toughradius.modules import models
from urllib import urlencode
from toughradius.common import tools
from toughradius.modules.events.settings import ISSUES_ASSIGN_EVENT
from twisted.internet.threads import deferToThread
import base64

@permit.route('/mps/issues')

class MpsIssuesHandler(BaseHandler):

    def get(self):
        openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
        if not openid:
            cbk_param = urlencode({'cbk': '/mps/issues'})
            return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
        customer = self.db.query(models.TrCustomer).filter_by(wechat_oid=openid).first()
        if not customer:
            return self.redirect('/mps/userbind', permanent=False)
        self.render('mps_issues_form.html')


@permit.route('/mps/issues/add')

class MpsIssuesAddHandler(BaseHandler):

    def get_builder_phone(self, builder_name):
        return self.db.query(models.TrBuilder.builder_phone).filter_by(builder_name=builder_name).scalar()

    def notify_builder(self, issues):
        builder_phone = self.get_builder_phone(issues.builder_name)
        if builder_phone:
            dispatch.pub(ISSUES_ASSIGN_EVENT, issues.account_number, builder_phone, async=True)

    def notify_user(self, oid, content):
        func = lambda : self.wechat.send_text_message(oid, content)
        deferd = deferToThread(func)
        deferd.addErrback(logger.exception)

    def post(self):
        try:
            openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
            if not openid:
                cbk_param = urlencode({'cbk': '/mps/issues'})
                return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
            customer = self.db.query(models.TrCustomer).filter_by(wechat_oid=openid).first()
            if not customer:
                return self.redirect('/mps/userbind', permanent=False)
            issues_type = self.get_argument('issues_type', '')
            content = self.get_argument('content', '')[:512]
            account = self.db.query(models.TrAccount).filter_by(customer_id=customer.customer_id).first()
            if self.db.query(models.TrIssues).filter_by(account_number=account.account_number, status=0).count() >= 7:
                return self.render('error.html', msg=u'您还有多条未受理完的工单，请耐心等待！')
            issues = models.TrIssues()
            issues.id = tools.gen_num_id(16)
            issues.account_number = account.account_number
            issues.issues_type = issues_type
            issues.content = content
            issues.builder_name = self.get_param_value('mps_issues_builder', 'default')
            issues.status = 0
            issues.operator_name = 'admin'
            issues.date_time = utils.get_currtime()
            issues.sync_ver = tools.gen_sync_ver()
            self.db.add(issues)
            self.db.commit()
            self.notify_builder(issues)
            self.notify_user(customer.wechat_oid, u'尊敬的用户，您的工单已提交，我们会尽快处理，请耐心等待。')
            self.render('success.html', msg=u'在线受理完成')
        except Exception as err:
            logger.exception(err, trace='wechat')
            self.render('error.html', msg=u'在线受理失败，请联系客服 %s' % repr(err))