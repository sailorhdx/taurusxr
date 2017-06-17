#!/usr/bin/env python
# coding=utf-8
import re
import traceback
from hashlib import md5
from toughradius.toughlib import utils, logger
from toughradius.modules.base import BaseHandler
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.toughlib.storage import Storage
from toughradius.modules.settings import *
from toughradius.modules.hgboss.base import WsBaseHandler, Codes
from toughradius.modules.dbservice.customer_add import CustomerAdd
from toughradius.modules.dbservice.account_change import AccountChange
from toughradius.modules.dbservice.account_service import AccountService

@permit.route('/interface/businessgw')

class BusinessGwHandler(WsBaseHandler):
    methods = ('userReg', 'userUnReg', 'userProductModify', 'userPause', 'userResume', 'userMove')

    def userReg(self, wsbody):
        formdata = Storage()
        formdata.node_id = self.get_ws_attr(wsbody, 'areaCode')
        formdata.area_id = self.get_ws_attr(wsbody, 'courtyardCode', defval='')
        formdata.customer_id = self.get_ws_attr(wsbody, 'userName', notnull=True)
        formdata.account_number = self.get_ws_attr(wsbody, 'userName', notnull=True)
        formdata.password = self.get_ws_attr(wsbody, 'password', notnull=True)
        formdata.realname = self.get_ws_attr(wsbody, 'realName')
        formdata.product_id = self.get_ws_attr(wsbody, 'productCode', notnull=True)
        formdata.expire_date = self.get_ws_attr(wsbody, 'authEndDate', notnull=True)
        formdata.address = self.get_ws_attr(wsbody, 'installAddress')
        formdata.ip_address = self.get_ws_attr(wsbody, 'ipAddress')
        formdata.mobile = self.get_ws_attr(wsbody, 'mobile')
        formdata.idcard = self.get_ws_attr(wsbody, 'idcard')
        formdata.fee_value = 0
        formdata.giftdays = 0
        formdata.giftflows = 0
        formdata.agency_id = None
        formdata.charge_code = None
        formdata.months = 0
        formdata.status = 1
        formdata.builder_name = None
        formdata.customer_desc = 'BOSS\xe5\xbc\x80\xe9\x80\x9a\xe8\xb4\xa6\xe5\x8f\xb7'
        account = self.db.query(models.TrAccount).get(formdata.account_number)
        if account:
            return self.send_wsresp('userReg', code=Codes.ERROR_ALREADY_EXIST, UserCode='', error=u'\u7528\u6237\u5df2\u7ecf\u5b58\u5728')
        else:
            cmanager = CustomerAdd(self.db, self.aes)
            ret = cmanager.add(formdata)
            if not ret:
                self.send_wsresp('userReg', code=Codes.ERROR_UNKNOWN, UserCode='', error=cmanager.last_error)
            else:
                self.send_wsresp('userReg', code=Codes.SUCCESS, UserCode=formdata.account_number.strip())
            return

    def userUnReg(self, wsbody):
        customer_id = self.get_ws_attr(wsbody, 'userCode', notnull=True)
        account = self.db.query(models.TrAccount).filter_by(customer_id=customer_id).first()
        if not account:
            return self.send_wsresp('userReg', code=Codes.ERROR_NOT_EXIST, error=u'\u7528\u6237\u4e0d\u5b58\u5728')
        manager = AccountService(self.db, self.aes)
        if not manager.delete(account.account_number):
            self.send_wsresp('userUnReg', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('userUnReg', code=Codes.SUCCESS)

    def userProductModify(self, wsbody):
        customer_id = self.get_ws_attr(wsbody, 'userCode', notnull=True)
        account = self.db.query(models.TrAccount).filter_by(customer_id=customer_id).first()
        if not account:
            return self.send_wsresp('userReg', code=Codes.ERROR_NOT_EXIST, error=u'\u7528\u6237\u4e0d\u5b58\u5728')
        formdata = Storage()
        formdata.account_number = account.account_number
        formdata.product_id = self.get_ws_attr(wsbody, 'productCode', notnull=True)
        formdata.add_value = 0
        formdata.expire_date = account.expire_date
        formdata.balance = 0
        formdata.time_length = 0
        formdata.flow_length = 0
        formdata.operate_desc = u'SOAPAPI userProductModify'
        manager = AccountChange(self.db, self.aes)
        if not manager.change(formdata):
            self.send_wsresp('userProductModify', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('userProductModify', code=Codes.SUCCESS)

    def userPause(self, wsbody):
        customer_id = self.get_ws_attr(wsbody, 'userCode', notnull=True)
        account = self.db.query(models.TrAccount).filter_by(customer_id=customer_id).first()
        if not account:
            return self.send_wsresp('userReg', code=Codes.ERROR_NOT_EXIST, error=u'\u7528\u6237\u4e0d\u5b58\u5728')
        manager = AccountService(self.db, self.aes)
        if not manager.pause(account.account_number):
            self.send_wsresp('userPause', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('userPause', code=Codes.SUCCESS)

    def userResume(self, wsbody):
        customer_id = self.get_ws_attr(wsbody, 'userCode', notnull=True)
        account = self.db.query(models.TrAccount).filter_by(customer_id=customer_id).first()
        if not account:
            return self.send_wsresp('userReg', code=Codes.ERROR_NOT_EXIST, error=u'\u7528\u6237\u4e0d\u5b58\u5728')
        manager = AccountService(self.db, self.aes)
        if not manager.resume(account.account_number):
            self.send_wsresp('userResume', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('userResume', code=Codes.SUCCESS)

    def userMove(self, wsbody):
        self.send_wsresp('userMove', code=Codes.SUCCESS)