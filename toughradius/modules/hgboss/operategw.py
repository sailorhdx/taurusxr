#!/usr/bin/env python
# coding=utf-8
import re
import traceback
from hashlib import md5
from toughradius.toughlib import utils, logger, dispatch
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.common import tools
from toughradius.modules import models
from toughradius.toughlib.storage import Storage
from toughradius.modules.settings import *
from toughradius.modules.hgboss.base import WsBaseHandler, Codes
from toughradius.modules.dbservice.customer_add import CustomerAdd
from toughradius.modules.dbservice.account_change import AccountChange
from toughradius.modules.dbservice.product_service import ProductService
from toughradius.modules.dbservice.node_service import NodeService
from toughradius.modules.dbservice.account_service import AccountService

@permit.route('/interface/operategw')

class OperateGwHandler(WsBaseHandler):
    methods = ('insertArea', 'updateArea', 'deleteArea', 'insertProduct', 'updateProduct', 'deleteProduct', 'queryUserBind', 'userReleaseBind', 'userUnlock', 'userModify', 'userOnlineQuery', 'userPasswordUpdate', 'updatePolicy')

    def insertArea(self, wsbody):
        formdata = Storage()
        formdata.node_id = self.get_ws_attr(wsbody, 'areaCode', notnull=True)
        formdata.node_name = self.get_ws_attr(wsbody, 'areaName', notnull=True)
        formdata.node_desc = u'BOSS 接入区域'
        formdata.rule_id = 0
        node = self.db.query(models.TrNode).get(formdata.node_id)
        if node:
            return self.send_wsresp('insertArea', code=Codes.ERROR_ALREADY_EXIST, error=u'区域已经存在')
        manager = NodeService(self.db, self.aes)
        ret = manager.add(formdata)
        if not ret:
            self.send_wsresp('insertArea', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('insertArea', code=Codes.SUCCESS)

    def updateArea(self, wsbody):
        formdata = Storage()
        formdata.id = self.get_ws_attr(wsbody, 'areaCode', notnull=True)
        formdata.node_name = self.get_ws_attr(wsbody, 'areaName', notnull=True)
        formdata.node_desc = u'BOSS 接入区域'
        formdata.rule_id = 0
        node = self.db.query(models.TrNode).get(formdata.id)
        if not node:
            return self.send_wsresp('updateArea', code=Codes.ERROR_ALREADY_EXIST, error=u'区域不存在')
        manager = NodeService(self.db, self.aes)
        ret = manager.update(formdata)
        if not ret:
            self.send_wsresp('updateArea', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('updateArea', code=Codes.SUCCESS)

    def deleteArea(self, wsbody):
        node_id = self.get_ws_attr(wsbody, 'areaCode', notnull=True)
        manager = NodeService(self.db, self.aes)
        ret = manager.delete(node_id)
        if not ret:
            self.send_wsresp('deleteArea', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('deleteArea', code=Codes.SUCCESS)

    def insertProduct(self, wsbody):
        formdata = Storage()
        formdata.product_id = self.get_ws_attr(wsbody, 'productCode', notnull=True)
        formdata.product_name = self.get_ws_attr(wsbody, 'productName', notnull=True)
        formdata.bind_mac = self.get_ws_attr(wsbody, 'bindMac', defval=0)
        formdata.bind_vlan = self.get_ws_attr(wsbody, 'bindVlan', defval=0)
        formdata.concur_number = self.get_ws_attr(wsbody, 'concurNumber', defval=0)
        formdata.bandwidthCode = self.get_ws_attr(wsbody, 'bandwidthCode', defval='')
        formdata.input_max_limit = utils.bb2mb(self.get_ws_attr(wsbody, 'inputMaxLimit', defval=0))
        formdata.output_max_limit = utils.bb2mb(self.get_ws_attr(wsbody, 'outputMaxLimit', defval=0))
        formdata.fee_months = self.get_ws_attr(wsbody, 'feeNum', defval=0)
        formdata.fee_price = self.get_ws_attr(wsbody, 'feePrice', defval=0)
        formdata.product_policy = BOMonth
        formdata.fee_times = 0
        formdata.fee_flows = 0
        formdata.product_charges = None
        formdata.free_auth = 0
        formdata.free_auth_uprate = 0
        formdata.free_auth_downrate = 0
        pkg = self.db.query(models.TrProduct).get(formdata.product_id)
        if pkg:
            return self.send_wsresp('insertProduct', code=Codes.ERROR_ALREADY_EXIST, error=u'套餐已经存在')
        else:
            manager = ProductService(self.db, self.aes)
            ret = manager.add(formdata)
            if not ret:
                self.send_wsresp('insertProduct', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
            else:
                self.send_wsresp('insertProduct', code=Codes.SUCCESS)
            return

    def updateProduct(self, wsbody):
        formdata = Storage()
        formdata.id = self.get_ws_attr(wsbody, 'productCode', notnull=True)
        product = self.db.query(models.TrProduct).get(formdata.id)
        if not product:
            return self.send_wsresp('updateProduct', code=Codes.ERROR_ALREADY_EXIST, error=u'套餐不存在')
        else:
            formdata.product_name = self.get_ws_attr(wsbody, 'productName', notnull=True)
            formdata.product_status = 0
            formdata.bind_mac = self.get_ws_attr(wsbody, 'bindMac', defval=0)
            formdata.bind_vlan = self.get_ws_attr(wsbody, 'bindVlan', defval=0)
            formdata.concur_number = self.get_ws_attr(wsbody, 'concurNumber', defval=0)
            formdata.bandwidthCode = self.get_ws_attr(wsbody, 'bandwidthCode', defval='')
            formdata.input_max_limit = utils.bb2mb(self.get_ws_attr(wsbody, 'inputMaxLimit', defval=0))
            formdata.output_max_limit = utils.bb2mb(self.get_ws_attr(wsbody, 'outputMaxLimit', defval=0))
            formdata.fee_months = product.fee_months
            formdata.fee_price = product.fee_price
            formdata.product_policy = BOMonth
            formdata.fee_times = product.fee_times
            formdata.fee_flows = product.fee_flows
            formdata.product_charges = None
            formdata.free_auth = product.free_auth
            formdata.free_auth_uprate = product.free_auth_uprate
            formdata.free_auth_downrate = product.free_auth_downrate
            manager = ProductService(self.db, self.aes)
            ret = manager.update(formdata)
            if not ret:
                self.send_wsresp('updateProduct', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
            else:
                self.send_wsresp('updateProduct', code=Codes.SUCCESS)
            return

    def deleteProduct(self, wsbody):
        product_id = self.get_ws_attr(wsbody, 'productCode', notnull=True)
        manager = ProductService(self.db, self.aes)
        ret = manager.delete(product_id)
        if not ret:
            self.send_wsresp('deleteProduct', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('deleteProduct', code=Codes.SUCCESS)

    def queryUserBind(self, wsbody):
        customer_id = self.get_ws_attr(wsbody, 'userCode', notnull=True)
        account = self.db.query(models.TrAccount).filter_by(customer_id=customer_id).first()
        if not account:
            return self.send_wsresp('queryUserBind', code=Codes.ERROR_NOT_EXIST, error=u'用户不存在')
        self.send_wsresp('queryUserBind', code=Codes.SUCCESS, MacAddress=account.mac_addr, VlanId1=account.vlan_id1, VlanId2=account.vlan_id2)

    def userReleaseBind(self, wsbody):
        customer_id = self.get_ws_attr(wsbody, 'userCode', notnull=True)
        account = self.db.query(models.TrAccount).filter_by(customer_id=customer_id).first()
        if not account:
            return self.send_wsresp('userReleaseBind', code=Codes.ERROR_NOT_EXIST, error=u'用户不存在')
        manager = AccountService(self.db, self.aes)
        ret = manager.release(account.account_number)
        if not ret:
            self.send_wsresp('userReleaseBind', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('userReleaseBind', code=Codes.SUCCESS)

    def userUnlock(self, wsbody):
        nas_addr = self.get_ws_attr(wsbody, 'basIpAddress')
        session_id = self.get_ws_attr(wsbody, 'acctSessionId')
        self.db.query(models.TrOnline).filter_by(nas_addr=nas_addr, acct_session_id=session_id).delete()
        self.send_wsresp('userUnlock', code=Codes.SUCCESS)

    def userModify(self, wsbody):
        formdata = Storage()
        formdata.customer_id = self.get_ws_attr(wsbody, 'userCode')
        formdata.realname = self.get_ws_attr(wsbody, 'realName')
        formdata.install_address = self.get_ws_attr(wsbody, 'installAddress')
        formdata.ip_address = self.get_ws_attr(wsbody, 'ipAddress')
        formdata.mobile = self.get_ws_attr(wsbody, 'mobile')
        formdata.idcard = self.get_ws_attr(wsbody, 'idcard')
        account = self.db.query(models.TrAccount).filter_by(customer_id=formdata.customer_id).first()
        if not account:
            return self.send_wsresp('userModify', code=Codes.ERROR_NOT_EXIST, error=u'用户不存在')
        formdata.account_number = account.account_number
        formdata.user_concur_number = account.user_concur_number
        formdata.bind_vlan = account.bind_vlan
        formdata.bind_mac = account.bind_mac
        formdata.account_desc = account.account_desc
        customer = self.db.query(models.TrCustomer).get(formdata.customer_id)
        customer.realname = formdata.realname
        customer.address = formdata.install_address
        customer.mobile = formdata.mobile
        customer.idcard = formdata.idcard
        manager = AccountService(self.db, self.aes)
        ret = manager.update(formdata)
        if not ret:
            self.send_wsresp('userModify', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('userModify', code=Codes.SUCCESS)

    def userOnlineQuery(self, wsbody):

        def send_result(onlines):
            if not onlines:
                return self.send_wsresp('userOnlineQuery', code=Codes.SUCCESS, PageNo=0, TotalNum=0)
            total = onlines.count()
            onarray = []
            for online in onlines:
                ol = ['<Online>']
                ol.append('<UserName>{}</UserName>'.format(online.account_number))
                ol.append('<BasIpAddress>{}</BasIpAddress>'.format(online.nas_addr))
                ol.append('<AcctSessionId>{}</AcctSessionId>'.format(online.acct_session_id))
                ol.append('<AcctStartTime>{}</AcctStartTime>'.format(online.acct_start_time))
                ol.append('<MacAddress>{}</MacAddress>'.format(online.mac_addr))
                ol.append('<IpAddress>{}</IpAddress>'.format(online.framed_ipaddr))
                ol.append('</Online>')
                onarray.append(''.join(ol))

            return self.send_wsresp('userOnlineQuery', code=Codes.SUCCESS, PageNo=1, TotalNum=total, OnlineList=''.join(onarray))

        customer_id = self.get_ws_attr(wsbody, 'userCode', notnull=True)
        if customer_id:
            account = self.db.query(models.TrAccount).filter_by(customer_id=customer_id).first()
            if not account:
                return self.send_wsresp('userOnlineQuery', code=Codes.SUCCESS, PageNo=0, TotalNum=0)
            onlines = self.db.query(models.TrOnline).filter_by(account_number=account.account_number).limit(100)
            send_result(onlines)
        else:
            onlines = self.db.query(models.TrOnline).limit(100)
            send_result(onlines)

    def userPasswordUpdate(self, wsbody):
        formdata = Storage()
        formdata.customer_id = self.get_ws_attr(wsbody, 'userCode')
        formdata.password = self.get_ws_attr(wsbody, 'password')
        account = self.db.query(models.TrAccount).filter_by(customer_id=formdata.customer_id).first()
        if not account:
            return self.send_wsresp('userPasswordUpdate', code=Codes.ERROR_NOT_EXIST, error=u'用户不存在')
        formdata.account_number = account.account_number
        manager = AccountService(self.db, self.aes)
        ret = manager.password(formdata)
        if not ret:
            self.send_wsresp('userPasswordUpdate', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('userPasswordUpdate', code=Codes.SUCCESS)

    def updatePolicy(self, wsbody):
        formdata = Storage()
        formdata.customer_id = self.get_ws_attr(wsbody, 'userCode')
        formdata.domain = self.get_ws_attr(wsbody, 'domainCode')
        formdata.bind_mac = self.get_ws_attr(wsbody, 'bindMac')
        formdata.bind_vlan = self.get_ws_attr(wsbody, 'bindVlan')
        formdata.user_concur_number = self.get_ws_attr(wsbody, 'concurNumber')
        account = self.db.query(models.TrAccount).filter_by(customer_id=formdata.customer_id).first()
        if not account:
            return self.send_wsresp('updatePolicy', code=Codes.ERROR_NOT_EXIST, error=u'用户不存在')
        formdata.account_number = account.account_number
        manager = AccountService(self.db, self.aes)
        ret = manager.update(formdata)
        if not ret:
            self.send_wsresp('updatePolicy', code=Codes.ERROR_UNKNOWN, error=manager.last_error)
        else:
            self.send_wsresp('updatePolicy', code=Codes.SUCCESS)