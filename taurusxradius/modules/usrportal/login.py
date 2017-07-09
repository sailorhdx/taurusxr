#!/usr/bin/env python
# coding=utf-8

from taurusxradius.modules.usrportal import login_forms
from taurusxradius.modules.usrportal.base import BaseHandler
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.modules import models


@permit.route('/usrportal/login')

class UsrPortalLoginHandler(BaseHandler):

    def get(self):
        if not self.current_user:
            form = login_forms.login_form()
            self.render('usrportal_login_form.html', form=form)
            return
        else:
            self.redirect('/usrportal/profile')
            return

    def post(self):
        form = login_forms.login_form()
        if not form.validates(source=self.get_params()):
            return self.render('usrportal_login_form.html', form=form)
        account_number = form.d.account_number
        password = form.d.password

        if not account_number:
            return self.render_json(code=1, msg=u'请填写用户名')
        if not password:
            return self.render_json(code=1, msg=u'请填写密码')

        account = self.db.query(models.TrAccount).get(account_number)
        if not account:
            return self.render_json(code=1, msg=u'账号不存在')
        if self.aes.decrypt(account.password) != password:
            return self.render_json(code=1, msg=u'密码错误')
        product = self.db.query(models.TrProduct).get(account.product_id)
        self.set_session_user(account.customer_id, account.account_number,
                              self.request.remote_ip, utils.get_currtime(),
                              account.status, account.expire_date, account.create_time,
                              product.product_policy, product.product_name)
        return self.render_json(code=0, msg='ok')

@permit.route('/usrportal/logout')

class UsrPortalLogout2Handler(BaseHandler):

    def get(self):
        if not self.current_user:
            self.redirect('/usrportal/login')
            return
        self.clear_session()
        self.redirect('/usrportal/login', permanent=False)