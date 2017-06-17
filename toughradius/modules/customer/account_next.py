#!/usr/bin/env python
# coding=utf-8
import decimal
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.customer import account, account_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch, db_cache
from toughradius.modules.settings import *
from toughradius.modules.dbservice.account_renew import AccountRenew

@permit.route('/admin/account/renew', u'用户续费或充值', MenuUser, order=2.3)

class AccountRenewHandler(account.AccountHandler):

    @authenticated
    def get(self):
        account_number = self.get_argument('account_number')
        policy = self.db.query(models.TrProduct.product_policy).filter(models.TrProduct.id == models.TrAccount.product_id, models.TrAccount.account_number == account_number).scalar()
        if policy in (PPMonth,
         PPDay,
         BOMonth,
         BODay,
         BOFlows,
         BOTimes):
            self.redirect('/admin/account/next?account_number=%s' % account_number)
        elif policy in (PPTimes, PPFlow, PPMFlows):
            self.redirect('/admin/account/charge?account_number=%s' % account_number)
        else:
            self.render_error(msg=u'该用户资费不支持续费')

@permit.route('/admin/account/next/uptime', u'用户续费调整时间', MenuUser, order=2.3001)

class AccountNextUptimeHandler(account.AccountHandler):

    def get(self):
        pass


@permit.route('/admin/account/next', u'用户续费', MenuUser, order=2.3)

class AccountNextHandler(account.AccountHandler):

    def get_expire_date(self, expire):
        if not utils.is_expire(expire):
            return expire
        renew_type = self.get_param_value('renew_time_type', '0')
        if renew_type == '0':
            return utils.get_currdate()
        elif renew_type == '1':
            return expire
        else:
            return utils.get_currdate()

    @authenticated
    def get(self):
        account_number = self.get_argument('account_number')
        user = self.query_account(account_number)
        form = account_forms.account_next_form()
        form.account_number.set_value(account_number)
        form.old_expire.set_value(self.get_expire_date(user.expire_date))
        form.product_id.set_value(user.product_id)
        return self.render('account_next_form.html', user=user, form=form)

    @authenticated
    def post(self):
        account_number = self.get_argument('account_number')
        user = self.query_account(account_number)
        form = account_forms.account_next_form()
        form.product_id.set_value(user.product_id)
        if not form.validates(source=self.get_params()):
            return render('account_next_form.html', user=user, form=form)
        manager = AccountRenew(self.db, self.aes, operator=self.current_user)
        if not manager.renew(form.d):
            return self.render('account_next_form.html', user=user, form=form, msg=manager.last_error)
        self.redirect(self.detail_url_fmt(account_number))