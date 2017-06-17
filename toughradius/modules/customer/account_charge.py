#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.customer import account, account_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch, db_cache
from toughradius.modules.settings import *
from toughradius.modules.dbservice.account_charge import AccountCharge
from toughradius.modules.events.settings import CACHE_DELETE_EVENT
from toughradius.common import tools

@permit.route('/admin/account/charge', u'用户充值', MenuUser, order=2.4)

class AccountChargeHandler(account.AccountHandler):

    @cyclone.web.authenticated
    def get(self):
        account_number = self.get_argument('account_number')
        user = self.query_account(account_number)
        form = account_forms.account_charge_form()
        form.account_number.set_value(account_number)
        return self.render('account_form.html', user=user, form=form)

    @cyclone.web.authenticated
    def post(self):
        account_number = self.get_argument('account_number')
        account = self.db.query(models.TrAccount).get(account_number)
        user = self.query_account(account_number)
        form = account_forms.account_charge_form()
        if account.status not in (1, 4):
            return render('account_form', user=user, form=form, msg=u'无效用户状态')
        if not form.validates(source=self.get_params()):
            return render('account_form', user=user, form=form)
        manager = AccountCharge(self.db, self.aes, operator=self.current_user)
        if not manager.charge(form.d):
            return self.render('account_form.html', user=user, form=form, msg=manager.last_error)
        self.redirect(self.detail_url_fmt(account_number))