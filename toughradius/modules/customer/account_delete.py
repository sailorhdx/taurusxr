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
from toughradius.modules.dbservice.account_service import AccountService

@permit.suproute('/admin/account/delete', u'用户账号删除', MenuUser, order=2.6)

class AccountDeleteHandler(account.AccountHandler):

    @authenticated
    def get(self):
        account_number = self.get_argument('account_number')
        if not account_number:
            self.render_error(msg=u'account_number is empty')
        manager = AccountService(self.db, self.aes)
        if not manager.delete(account_number):
            return self.render_error(msg=manager.last_error)
        return self.redirect('/admin/customer')