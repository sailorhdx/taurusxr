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
from taurusxradius.taurusxlib import utils, dispatch, db_cache, logger
from taurusxradius.modules.settings import *
from taurusxradius.modules.dbservice.account_cancel import AccountCancel

@permit.route('/admin/account/cancel', u'用户销户', MenuUser, order=2.7)

class AccountCanceltHandler(account.AccountHandler):

    @authenticated
    def get(self):
        account_number = self.get_argument('account_number')
        user = self.query_account(account_number)
        form = account_forms.account_cancel_form()
        form.account_number.set_value(account_number)
        return self.render('account_form.html', user=user, form=form)

    @authenticated
    def post(self):
        account_number = self.get_argument('account_number')
        account = self.db.query(models.TrAccount).get(account_number)
        user = self.query_account(account_number)
        form = account_forms.account_cancel_form()
        if not form.validates(source=self.get_params()):
            return self.render('account_form.html', user=user, form=form)
        manager = AccountCancel(self.db, self.aes, operator=self.current_user)
        if not manager.cancel(form.d):
            return self.render('account_form.html', user=user, form=form, msg=manager.last_error)
        self.redirect(self.detail_url_fmt(account_number))