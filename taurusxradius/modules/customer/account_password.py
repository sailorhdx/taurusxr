#!/usr/bin/env python
# coding=utf-8
from hashlib import md5
from taurusxradius.taurusxlib import utils, dispatch, redis_cache
from taurusxradius.modules.base import authenticated
from taurusxradius.modules.customer import account_forms
from taurusxradius.modules.customer import account
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules import models
from taurusxradius.modules.settings import *
from taurusxradius.common import tools
from taurusxradius.modules.dbservice.account_service import AccountService

@permit.route('/admin/account/password', u'用户账号密码修改', MenuUser, order=1.41, is_menu=False)

class PasswordUpdateHandler(account.AccountHandler):

    @authenticated
    def get(self):
        form = account_forms.password_update_form()
        form.fill(account_number=self.get_argument('account_number'))
        return self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = account_forms.password_update_form()
        if not form.validates(source=self.get_params()):
            self.render('base_form.html', form=form)
            return
        manager = AccountService(self.db, self.aes)
        if not manager.password(form.d):
            return self.render_error(msg=manager.last_error)
        self.redirect(self.detail_url_fmt(form.d.account_number))