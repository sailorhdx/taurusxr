#!/usr/bin/env python
# coding=utf-8
import datetime
import time
import json
import decimal
import string
from hashlib import md5

from taurusxradius.modules.dbservice.account_change import AccountChange
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.modules.usrportal.base import BaseHandler, authenticated
from taurusxradius.modules.usrportal import order_forms
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib.storage import Storage
from taurusxradius.modules import models
from taurusxradius.modules.dbservice.customer_add import CustomerAdd
from taurusxradius.modules.dbservice.account_renew import AccountRenew
from taurusxradius.modules.dbservice.account_charge import AccountCharge
from taurusxradius.modules.settings import order_paycaache_key

@permit.route('/usrportal/alipay/verify/(\\w+)')

class UsrPortalProductOrderVerifyHandler(BaseHandler):
    """ 支付宝支付第三步： 支付通知处理
    """

    def check_xsrf_cookie(self):
        pass

    def get_product_name(self, pid):
        return self.db.query(models.TrProduct.product_name).filter_by(id=pid).scalar()

    def get(self, order_type):
        isok = self.alipay.notify_verify(self.get_params())
        if not isok:
            logger.info(u'收到支付宝订单通知,订单校验无效', trace='alipay', **self.get_params())
            return self.render_error(code=1, msg=u'订单校验无效')
        order_id = self.get_argument('out_trade_no')
        order = self.db.query(models.TrCustomerOrder).get(order_id)
        if order and order.pay_status == 1:
            return self.render('profile_alipay_return.html', order=order)
        formdata = self.paycache.get(order_paycaache_key(order_id))
        if not formdata:
            logger.error(u'收到支付宝订单通知，但是本地查不到订单%s' % order_id, trace='alipay')
            return self.render_error(code=1, msg=u'订单不存在')
        ret = False
        if order_type == 'new':
            manager = CustomerAdd(self.db, self.aes)
            ret = manager.add(formdata)
        if order_type == 'renew':
            manager = AccountRenew(self.db, self.aes)
            ret = manager.renew(formdata)
        if order_type == 'charge':
            manager = AccountCharge(self.db, self.aes)
            ret = manager.charge(formdata)
        if ret:
            order = self.db.query(models.TrCustomerOrder).get(order_id)
            logger.info(u'收到支付宝订单通知，处理成功', trace='alipay', account_number=formdata.account_number, order_id=order_id)
            self.render('profile_alipay_return.html', order=order)
        else:
            return self.render_error(code=1, msg=u'订单处理失败 %s' % manager.last_error)

    def post(self, order_type):
        isok = self.alipay.notify_verify(self.get_params())
        if not isok:
            self.write('failure')
            logger.info(u'收到支付宝订单通知,订单无效', trace='alipay', **self.get_params())
            return
        order_id = self.get_argument('out_trade_no')
        if self.db.query(models.TrCustomerOrder).filter_by(order_id=order_id, pay_status=1).count() == 1:
            self.write('success')
            return
        formdata = self.paycache.get(order_paycaache_key(order_id))
        if not formdata:
            logger.error(u'收到支付宝订单通知，但是本地缓存查不到订单%s' % order_id, trace='alipay')
            self.write('failure')
            return
        ret = False
        if order_type == 'new':
            manager = CustomerAdd(self.db, self.aes)
            ret = manager.add(formdata)
        if order_type == 'renew':
            manager = AccountRenew(self.db, self.aes)
            ret = manager.renew(formdata)
        if order_type == 'charge':
            manager = AccountChange(self.db, self.aes)
            ret = manager.charge(formdata)
        if ret:
            self.write('success')
            logger.info(u'收到支付宝订单通知，处理成功', trace='alipay', account_number=formdata.account_number, order_id=formdata.order_id)
        else:
            logger.error(u'订单处理失败', trace='alipay')