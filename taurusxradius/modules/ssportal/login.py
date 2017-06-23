#!/usr/bin/env python
# coding=utf-8
import datetime
import time
from taurusxradius.modules.ssportal.base import BaseHandler
from taurusxradius.modules.ssportal import login_form
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils
from taurusxradius.modules import models

@permit.route('/ssportal/login')

class SSportalLoginHandler(BaseHandler):

    def get(self):
        form = login_form.login_form()
        self.render('base_form.html', form=form)

    def post(self):
        form = login_form.login_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        account = self.db.query(models.TrAccount).get(form.d.username)
        if not account:
            return self.render('base_form.html', form=form, msg=u'账号不存在')
        if self.aes.decrypt(account.password) != form.d.password:
            return self.render('base_form.html', form=form, msg=u'密码错误')
        self.set_session_user(account.customer_id, account.account_number, self.request.remote_ip, utils.get_currtime())
        self.redirect('/ssportal')