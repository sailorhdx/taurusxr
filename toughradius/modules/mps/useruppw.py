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
import json

@permit.route('/mps/modpwd')

class MpsUserUppwdHandler(BaseHandler):

    def get(self):
        openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
        if not openid:
            cbk_param = urlencode({'cbk': '/mps/modpwd'})
            return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
        customer = self.db.query(models.TrCustomer).filter_by(wechat_oid=openid).first()
        if not customer:
            return self.redirect('/mps/userbind', permanent=False)
        self.render('user_uppwd_form.html')

    def post(self):
        try:
            openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
            if not openid:
                return self.render('error.html', msg=u'会话过期')
            customer = self.db.query(models.TrCustomer).filter_by(wechat_oid=openid).first()
            if not customer:
                return self.render('error.html', msg=u'未绑定微信')
            oldpass = self.get_argument('oldpass', '')
            newpass = self.get_argument('newpass', '')
            newpass1 = self.get_argument('newpass1', '')
            if not oldpass:
                return self.render('error.html', msg=u'旧密码不能为空')
            if not rules.is_alphanum2(6, 16).valid(newpass):
                return self.render('error.html', msg=u'新密码校验错误,必须是6-16为的英文字符数字')
            if newpass != newpass1:
                return self.render('error.html', msg=u'确认密码不正确')
            account = self.db.query(models.TrAccount).filter_by(customer_id=customer.customer_id).first()
            if not account:
                return self.render('error.html', msg=u'用户名不存在')
            if account.status not in (0, 1):
                return self.render('error.html', msg=u'用户账号不在正常状态，有疑问请联系客服')
            if self.aes.decrypt(account.password) != oldpass:
                return self.render('error.html', msg=u'用户旧密码不正确')
            account.password = self.aes.encrypt(newpass.encode('utf-8'))
            self.db.commit()
            self.render('success.html', msg=u'修改密码成功')
        except Exception as err:
            logger.exception(err, trace='wechat')
            self.render('error.html', msg=u'修改密码失败，请联系客服 %s' % repr(err))