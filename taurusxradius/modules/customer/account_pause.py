#!/usr/bin/env python
#coding:utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
from taurusxradius.modules import models
from taurusxradius.modules.base import BaseHandler, authenticated
from taurusxradius.modules.customer import account, account_forms
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, dispatch, db_cache
from taurusxradius.modules.settings import *
from taurusxradius.modules.events.settings import ACCOUNT_PAUSE_EVENT
from taurusxradius.modules.events.settings import UNLOCK_ONLINE_EVENT
from taurusxradius.common import tools
from taurusxradius.modules.dbservice.account_service import AccountService

@permit.route('/admin/account/pause', u'用户停机', MenuUser, order=2.1)

class AccountPausetHandler(account.AccountHandler):

    @authenticated
    def post(self):
        account_number = self.get_argument('account_number')
        manager = AccountService(self.db, self.aes)
        if not manager.pause(account_number):
            return self.render_json(code=1, msg=manager.last_error)
        return self.render_json(msg=u'操作成功')