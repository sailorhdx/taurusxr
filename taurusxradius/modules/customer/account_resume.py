#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
from taurusxradius.modules import models
from taurusxradius.modules.base import BaseHandler, authenticated
from taurusxradius.modules.customer import account
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, dispatch, db_cache
from taurusxradius.modules.settings import *
from taurusxradius.common import tools
from taurusxradius.modules.dbservice.account_service import AccountService

@permit.route('/admin/account/resume', u'用户复机', MenuUser, order=2.1)

class AccountResumetHandler(account.AccountHandler):

    @cyclone.web.authenticated
    def post(self):
        account_number = self.get_argument('account_number')
        manager = AccountService(self.db, self.aes)
        if not manager.resume(account_number):
            return self.render_json(code=1, msg=manager.last_error)
        return self.render_json(msg=u'操作成功')