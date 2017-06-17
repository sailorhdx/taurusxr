#!/usr/bin/env python
# coding=utf-8
import time
import traceback
from toughradius.toughlib import utils, apiutils, dispatch, logger
from toughradius.toughlib.permit import permit
from toughradius.modules.api.apibase import ApiHandler
from toughradius.modules.api.apibase import authapi
from toughradius.modules import models
from toughradius.modules.dbservice.account_service import AccountService

@permit.route('/api/v1/account/query')

class AccountUpdateApiHandler(ApiHandler):

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            if not formdata:
                return
            account_number = formdata.get('account_number')
            mac_addr = formdata.get('mac_addr')
            product_id = formdata.get('product_id')
            accounts = self.db.query(models.TrAccount)
            if account_number:
                accounts = accounts.filter_by(account_number=account_number)
            if mac_addr:
                accounts = accounts.filter_by(mac_addr=mac_addr)
            if product_id:
                accounts = accounts.filter_by(product_id=product_id)
            account_datas = []
            for account in accounts:
                account_data = {c.name:getattr(account, c.name) for c in account.__table__.columns}
                account_datas.append(account_data)

            self.render_success(data=account_datas)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)


@permit.route('/api/v1/account/update')

class AccountUpdateApiHandler(ApiHandler):

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            if not formdata:
                return
            service = AccountService(self.db, self.aes)
            ret = service.update(formdata)
            if ret:
                return self.render_success()
            return self.render_server_err(msg=service.last_error)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)


@permit.route('/api/v1/account/password/update')

class AccountUpdatePasswordApiHandler(ApiHandler):

    def get(self):
        self.post()

    def post(self):
        try:
            formdata = self.parse_form_request()
            if not formdata:
                return
            service = AccountService(self.db, self.aes)
            ret = service.password(formdata)
            if ret:
                return self.render_success()
            return self.render_server_err(msg=service.last_error)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)


@permit.route('/api/v1/account/delete')

class AccountDeleteApiHandler(ApiHandler):

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            if not formdata:
                return
            service = AccountService(self.db, self.aes)
            ret = service.delete(formdata.account_number)
            if ret:
                return self.render_success()
            return self.render_server_err(msg=service.last_error)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)


@permit.route('/api/v1/account/release')

class AccountReleaseApiHandler(ApiHandler):

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            if not formdata:
                return
            service = AccountService(self.db, self.aes)
            ret = service.release(formdata.account_number)
            if ret:
                return self.render_success()
            return self.render_server_err(msg=service.last_error)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)


@permit.route('/api/v1/account/pause')

class AccountPauseApiHandler(ApiHandler):

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            if not formdata:
                return
            service = AccountService(self.db, self.aes)
            ret = service.pause(formdata.account_number)
            if ret:
                return self.render_success()
            return self.render_server_err(msg=service.last_error)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)


@permit.route('/api/v1/account/resume')

class AccountPauseApiHandler(ApiHandler):

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            if not formdata:
                return
            service = AccountService(self.db, self.aes)
            ret = service.resume(formdata.account_number)
            if ret:
                return self.render_success()
            return self.render_server_err(msg=service.last_error)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)