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
from toughradius.modules.dbservice.account_change import AccountChange

@permit.route('/admin/account/change/get_policy')

class AccountChangePolicyGetHandler(account.AccountHandler):

    @authenticated
    def get(self):
        product_id = self.get_argument('product_id')
        product_policy = self.db.query(models.TrProduct.product_policy).filter_by(id=product_id).scalar()
        return self.render_json(data={'id': product_id,
         'policy': product_policy})


@permit.route('/admin/account/change', u'用户变更资费', MenuUser, order=2.5)

class AccountChangeHandler(account.AccountHandler):

    def get_cproducts(self):
        return [ (n.id, n.product_name) for n in self.get_opr_products() ]

    @authenticated
    def get(self):
        account_number = self.get_argument('account_number')
        products = self.get_cproducts()
        user = self.query_account(account_number)
        form = account_forms.account_change_form(products=products)
        form.expire_date.set_value(user.expire_date)
        form.account_number.set_value(account_number)
        return self.render('account_change_form.html', user=user, form=form)

    @authenticated
    def post(self):
        account_number = self.get_argument('account_number')
        products = self.get_cproducts()
        form = account_forms.account_change_form(products=products)
        user = self.query_account(account_number)
        if not form.validates(source=self.get_params()):
            return self.render('account_change_form.html', user=user, form=form)
        manager = AccountChange(self.db, self.aes, operator=self.current_user)
        if not manager.change(form.d):
            return self.render('account_change_form.html', user=user, form=form, msg=manager.last_error)
        self.redirect(self.detail_url_fmt(account_number))