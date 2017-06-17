#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.toughlib import logger
from toughradius.toughlib import utils
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.permit import permit
from toughradius.modules.mps.base import BaseHandler
from twisted.internet import defer
from toughradius.modules import models
from urllib import urlencode
from toughradius.common import tools
import base64

@permit.route('/mps/userbind')

class MpsUserbindHandler(BaseHandler):

    def get(self):
        openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
        if not openid:
            cbk_param = urlencode({'cbk': '/mps/userbind'})
            return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
        customer = self.db.query(models.TrCustomer).filter_by(wechat_oid=openid).first()
        if customer:
            self.redirect('/mps/userinfo', permanent=False)
        else:
            self.render('mps_bind_form.html', openid=openid)

    def post(self):
        try:
            openid = self.get_argument('openid', '')
            customer = self.db.query(models.TrCustomer).filter_by(wechat_oid=openid).first()
            if customer:
                return self.redirect('/mps/userinfo', permanent=False)
            username = self.get_argument('username', '')
            password = self.get_argument('password', '')
            account = self.db.query(models.TrAccount).get(username)
            if not account:
                return self.render('mps_bind_form.html', msg=u'用户名不存在')
            if self.aes.decrypt(account.password) != password:
                return self.render('mps_bind_form.html', msg=u'用户名与密码不符')
            if account.status not in (0, 1):
                return self.render('mps_bind_form.html', msg=u'用户账号不在正常状态，有疑问请联系客服', isp_code=account.status)
            customer = self.db.query(models.TrCustomer).get(account.customer_id)
            customer.wechat_oid = openid
            self.db.commit()
            self.render('success.html', msg=u'微信绑定成功')
        except Exception as err:
            logger.exception(err, trace='wechat')
            self.render('error.html', msg=u'微信绑定失败，请联系客服 %s' % repr(err))


@permit.route('/mps/userunbind')

class MpsUserUnbindHandler(BaseHandler):

    def get(self):
        openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
        if not openid:
            cbk_param = urlencode({'cbk': '/mps/userunbind'})
            return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
        customer = self.db.query(models.TrCustomer).filter_by(wechat_oid=openid).first()
        if customer:
            customer.wechat_oid = ''
            self.db.commit()
        self.render('success.html', msg=u'微信解绑成功')