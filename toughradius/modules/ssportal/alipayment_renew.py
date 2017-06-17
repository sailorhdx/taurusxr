#!/usr/bin/env python
# coding=utf-8
import datetime
import time
import json
import decimal
import string
import base64
from hashlib import md5
from toughradius.toughlib import utils, logger
from toughradius.modules.ssportal.base import BaseHandler, authenticated
from toughradius.modules.ssportal import order_forms
from toughradius.modules.ssportal import alipayment_new
from toughradius.toughlib.permit import permit
from toughradius.toughlib.storage import Storage
from toughradius.modules import models
from toughradius.common import tools
from toughradius.modules.dbservice.account_renew import AccountRenew
from toughradius.modules.settings import order_paycaache_key
from toughradius.modules.settings import PPMonth, BOMonth, BOTimes, BOFlows, MAX_EXPIRE_DATE

@permit.route('/ssportal/product/renew')

class SSportalRenewOrderHandler(alipayment_new.BasicOrderHandler):
    """ 发起续费支付
    """

    def get_expire_date(self, expire):
        if utils.is_expire(expire):
            return utils.get_currdate()
        else:
            return expire

    @authenticated
    def get(self):
        account_number = self.current_user.username
        account = self.db.query(models.TrAccount).get(account_number)
        product_id = account.product_id
        product = self.db.query(models.TrProduct).get(product_id)
        if not product:
            return self.render_alert(u'错误提示', u'套餐不存在')
        if product.product_status == 1:
            return self.render_alert(u'错误提示', u'套餐已停用')
        form = order_forms.renew_form(product.product_policy)
        form.account_number.set_value(account_number)
        form.product_id.set_value(product_id)
        form.product_name.set_value(product.product_name)
        self.render('renew_modal_form.html', form=form)

    def post(self):
        product_id = self.get_argument('product_id')
        product = self.db.query(models.TrProduct).get(product_id)
        form = order_forms.renew_form(product.product_policy)
        if not form.validates(source=self.get_params()):
            return self.render_json(code=1, msg=form.errors)
        account = self.db.query(models.TrAccount).get(form.d.account_number)
        if not account:
            return self.render_json(code=1, msg=u'账号不存在')
        try:
            _feevalue, _expire = self.order_calc(account.product_id, old_expire=self.get_expire_date(account.expire_date))
            order_id = utils.gen_order_id()
            formdata = Storage(form.d)
            formdata['order_id'] = order_id
            formdata['product_id'] = account.product_id
            formdata['fee_value'] = _feevalue
            formdata['expire_date'] = _expire
            formdata['accept_source'] = 'ssportal'
            formdata['giftdays'] = 0
            formdata['operate_desc'] = u'用户自助续费'
            formdata['old_expire'] = account.expire_date
            if form.d.vcard_code and form.d.vcard_pwd:
                formdata['vcard_code'] = form.d.vcard_code
                formdata['vcard_pwd'] = form.d.vcard_pwd
                manager = AccountRenew(self.db, self.aes)
                ret = manager.renew(formdata)
                if ret:
                    logger.info(u'充值卡续费成功')
                    self.render_json(code=100, msg=u'充值卡续费成功')
                else:
                    return self.render_json(code=1, msg=u'充值卡订单处理失败 %s' % manager.last_error)
            else:
                self.paycache.set(order_paycaache_key(order_id), formdata)
                self.render_json(code=0, msg=u'订单创建成功', order_id=order_id)
        except Exception as err:
            logger.exception(err)
            return self.render_json(code=0, msg=u'无效的订单')


@permit.route('/ssportal/product/renew/alipay')

class SSportalProductRenewHandler(BaseHandler):
    """ 支付信息确认，跳转支付宝
    """

    def get_product_name(self, pid):
        return self.db.query(models.TrProduct.product_name).filter_by(id=pid).scalar()

    @authenticated
    def get(self):
        order_id = self.get_argument('order_id', '')
        if not order_id:
            return self.render_error(code=1, msg=u'订单不存在')
        formdata = self.paycache.get(order_paycaache_key(order_id))
        if not formdata:
            return self.render_error(code=1, msg=u'订单已过期')
        try:
            formdata.order_id = order_id
            self.render('renew_alipay.html', formdata=formdata)
        except Exception as err:
            logger.exception(err)
            self.render_error(msg=u'订单处理错误，请联系管理员')

    @authenticated
    def post(self):
        order_id = self.get_argument('order_id')
        formdata = self.paycache.get(order_paycaache_key(order_id))
        product_name = self.get_product_name(formdata.product_id)
        self.redirect(self.alipay.create_direct_pay_by_user(order_id, u'套餐续费：%s' % product_name, product_name, formdata.fee_value, notify_path='/ssportal/alipay/verify/renew', return_path='/ssportal/alipay/verify/renew'))