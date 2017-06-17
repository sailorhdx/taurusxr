#!/usr/bin/env python
# coding=utf-8
import datetime
import time
from toughradius.modules.ssportal.base import BaseHandler, authenticated
from toughradius.modules.ssportal import password_form
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules import models

@permit.route('/ssportal/password/update')

class SSportalPasswordHandler(BaseHandler):

    @authenticated
    def get(self):
        form = password_form.password_form()
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = password_form.password_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        account_number = self.current_user.username
        account = self.db.query(models.TrAccount).get(account_number)
        if not account:
            return self.render('base_form.html', form=form, msg=u'账号不存在')
        if self.aes.decrypt(account.password) != form.d.opassword:
            return self.render('base_form.html', form=form, msg=u'旧密码错误')
        if form.d.npassword != form.d.cpassword:
            return self.render('base_form.html', form=form, msg=u'确认密码错误')
        account.password = self.aes.encrypt(form.d.cpassword)
        self.db.commit()
        self.redirect('/ssportal')