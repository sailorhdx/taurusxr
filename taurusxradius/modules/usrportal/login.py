#!/usr/bin/env python
# coding=utf-8
import datetime
import time

from taurusxradius.modules.customer import customer_forms
from taurusxradius.modules.dbservice.customer_add import CustomerAdd
from taurusxradius.modules.usrportal.base import BaseHandler
from taurusxradius.modules.usrportal import login_form
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.modules import models

@permit.route('/usrportal/login')

class UsrPortalLogin2Handler(BaseHandler):

    def get(self):
        self.render('usrportal_login.html')

    def post(self):
        uUsername = self.get_argument('username', '')
        uPassword = self.get_argument('password', '')

        if not uUsername:
            return self.render_json(code=1, msg=u'请填写用户名')
        if not uPassword:
            return self.render_json(code=1, msg=u'请填写密码')


        account = self.db.query(models.TrAccount).get(uUsername)
        if not account:
            return self.render_json(code=1, msg=u'账号不存在')
        if self.aes.decrypt(account.password) != uPassword:
            return self.render_json(code=1, msg=u'密码错误')
        self.set_session_user(account.customer_id, account.account_number, self.request.remote_ip, utils.get_currtime(), account.status, account.expire_date, account.create_time)
        self.render_json(code=0, msg='ok')

@permit.route('/usrportal/register')

class UsrPortalRegister2Handler(BaseHandler):

    def get(self):
        self.render('usrportal_register.html')

    def post(self):
        uUsername = self.get_argument('username', '')
        uPassword = self.get_argument('password', '')
        uConfirmpassword = self.get_argument('confirmpassword', '')
        uEmail = self.get_argument('email', '')

        if not uUsername:
            return self.render_json(code=1, msg=u'请填写用户名')
        if not uPassword:
            return self.render_json(code=1, msg=u'请填写密码')
        if uPassword <> uConfirmpassword:
            return self.render_json(code=1, msg=u'两次密码输入不一致')
        if not uEmail:
            return self.render_json(code=1, msg=u'请填写电子邮件')
        account = self.db.query(models.TrAccount).get(uUsername)
        if account:
            return self.render_json(code=1, msg=u'用户名[%s]已经存在' % (uUsername))

        nodes = [["1", "默认区域"]]
        products = [["014E7F784D2311E79C5EFA163EFD1A3E", "1小时测试资费"], ["04CDC64C51A911E7931EFA163EFD1A3E", "30天买断时长套餐"],
                   ["475FCEF04FE311E7931EFA163EFD1A3E", "3分钟测试"]]
        agencies = [["", ""]]


        form = customer_forms.customer_fast_open_form(nodes, products, agencies)

        cmanager = CustomerAdd(self.db, self.aes)

        ret = cmanager.add_account_from_portal(uUsername, uPassword, uEmail)
        # .add_account_from_portal(uUsername, uPassword, uEmail)
        if not ret:
            return self.render_json(code=1, msg=cmanager.last_error)
        self.db.commit()
        self.render_json(code=0, msg='ok')

@permit.route('/usrportal/forgot')

class UsrPortalForgot2Handler(BaseHandler):

    def get(self):
        self.render('usrportal_forgot.html')

    def post(self):
        uUsername = self.get_argument('username', '')
        uEmail = self.get_argument('email', '')
        if not uUsername:
            return self.render_json(code=1, msg=u'请填写用户名')
        if not uEmail:
            return self.render_json(code=1, msg=u'请填写电子邮件')
        account = self.db.query(models.TrAccount).get(uUsername)
        if not account:
            return self.render_json(code=1, msg=u'用户名[%s]不存在' % (uUsername))
        self.render_json(code=0, msg='ok')

@permit.route('/usrportal/logout')

class UsrPortalLogout2Handler(BaseHandler):

    def get(self):
        if not self.current_user:
            self.redirect('/usrportal/login')
            return
        self.clear_session()
        self.redirect('/usrportal/login', permanent=False)