#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
from taurusxradius.modules import models
from taurusxradius.modules.base import BaseHandler, authenticated
from taurusxradius.modules.customer import account, account_forms
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, dispatch, db_cache
from taurusxradius.modules.settings import *
from taurusxradius.common import tools
from taurusxradius.modules.dbservice.account_service import AccountService

@permit.route('/admin/account/update', u'用户策略修改', MenuUser, order=2.2)

class AccountUpdatetHandler(account.AccountHandler):

    @authenticated
    def get(self):
        account_number = self.get_argument('account_number', None)
        account = self.db.query(models.TrAccount).get(account_number)
        form = account_forms.account_update_form()
        form.fill(account)
        self.render('base_form.html', form=form)
        return

    @authenticated
    def post(self):
        form = account_forms.account_update_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        manager = AccountService(self.db, self.aes)
        if not manager.update(form.d):
            return self.render_error(msg=manager.last_error)
        self.redirect(self.detail_url_fmt(form.d.account_number))