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

@permit.route('/admin/account/release', u'用户解绑', MenuUser, order=2.8)

class AccountReleasetHandler(account.AccountHandler):

    @authenticated
    def post(self):
        account_number = self.get_argument('account_number')
        manager = AccountService(self.db, self.aes)
        if not manager.release(account_number):
            return self.render_json(code=1, msg=manager.last_error)
        return self.render_json(msg=u'解绑成功')