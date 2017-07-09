#!/usr/bin/env python
# coding=utf-8
import datetime
import time
import os
import json
import decimal
import string
import urllib
import base64
from hashlib import md5

from taurusxradius.modules.dbservice.account_renew import AccountRenew
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.common import safefile
from taurusxradius.common import tools
from taurusxradius.common import smsapi
from twisted.internet import reactor, defer
from cyclone import httpclient
from taurusxradius.modules.usrportal.base import BaseHandler, authenticated
from taurusxradius.modules.usrportal import order_forms
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib.storage import Storage
from taurusxradius.modules import models
from taurusxradius.modules.dbservice.customer_add import CustomerAdd
from taurusxradius.modules.settings import order_paycaache_key
from taurusxradius.modules.settings import PPMonth, PPTimes, BOMonth, BOTimes, PPFlow, BOFlows, PPMFlows, APMonth, PPDay, BODay, MAX_EXPIRE_DATE, VcodeNotify
product_policys = {#移除资费类型：预付费时长，预付费流量，预付费流量包月
    BOMonth: u'买断包月', #2
    BOTimes: u'买断时长', #3
    BOFlows: u'买断流量', #5
    #PPMFlows u'预付费流量包月', #7
    #APMonth: u'后付费包月', #8
    #PPMonth: u'预付费包月', #0
    #PPTimes: u'预付费时长', #1
    #PPDay: u'预付费包日', #9
    # PPFlow: u'预付费流量', #4
    BODay: u'买断包日' #10
}

@permit.route('/usrportal/product')

class UsrPortalProductHandler(BaseHandler):

    def get(self):
        types = [BOMonth,
         BOFlows,
         BOTimes,
         PPMonth,
         PPDay,
         BODay]
        products = self.db.query(models.TrProduct).filter(models.TrProduct.product_policy.in_(types), models.TrProduct.ispub == 1)
        self.render('profile_product.html', products=products, policys=product_policys)


class BasicOrderHandler(BaseHandler):

    def gen_account_number(self):
        node_id = self.get_param_value('default_user_node_id', 1)
        node = self.db.query(models.TrNode).get(node_id)
        rule = self.db.query(models.TrAccountRule).get(node.rule_id)
        rule.user_sn = rule.user_sn + 1
        self.db.commit()
        account_number = '%s%s' % (rule.user_prefix, string.rjust(str(rule.user_sn), rule.user_suffix_len, '0'))
        return account_number

@permit.route('/usrportal/product/order')

class UsrPortalProductOrderHandler(BasicOrderHandler):
    """  支付宝支付第一步：进入订购表单，发起订购支付
    """

    def get_product_name(self, pid):
        return self.db.query(models.TrProduct.product_name).filter_by(id=pid).scalar()

    def get(self):
        product_id = self.get_argument('product_id')
        product = self.db.query(models.TrProduct).get(product_id)
        if not product:
            self.render_error(msg=u'套餐不存在')
            return
        account_number = self.get_argument('account_number', '')
        if account_number and self.db.query(models.TrAccount).get(account_number):
            form = order_forms.smsvcode_form(product_id, account_number)
            self.render('profile_order_smsvcode_form.html', form=form, msg=u'手机号码已经注册')
            return
        smsvcode = self.get_argument('vcode', '')
        if account_number and not smsvcode:
            form = order_forms.smsvcode_form(product_id, account_number)
            self.render('profile_order_smsvcode_form.html', form=form, msg=u'验证码不能为空')
            return
        if account_number and smsvcode and self.cache.get('ssportal.sms.vcode.{}'.format(account_number)) != smsvcode:
            form = order_forms.smsvcode_form(product_id, account_number)
            self.render('profile_order_smsvcode_form.html', form=form, msg=u'验证码不匹配')
            return
        is_smsvcode = int(self.get_param_value('usrportal_smsvcode_required', 0))
        if not account_number and is_smsvcode:
            form = order_forms.smsvcode_form(product_id, '')
            self.render('profile_order_smsvcode_form.html', form=form)
            return
        account_number = account_number or self.gen_account_number()
        form = order_forms.order_form(product.product_policy)
        form.product_id.set_value(product_id)
        form.product_name.set_value(product.product_name)
        form.months.set_value(product.fee_months)
        form.days.set_value(product.fee_days)
        form.account_number.set_value(account_number)
        self.render('profile_neworder_form.html', form=form)

    def do_vcard(self, form, product):
        vcard_code = form.d.vcard_code
        vcard_pwd = form.d.vcard_pwd
        _feevalue, _expire = self.order_calc(form.d.product_id)
        order_id = utils.gen_order_id()
        formdata = Storage(form.d)
        formdata.order_id = order_id
        formdata['node_id'] = self.get_param_value('default_user_node_id', 1)
        formdata['area_id'] = ''
        formdata['fee_value'] = _feevalue
        formdata['expire_date'] = _expire
        formdata['accept_source'] = 'ssportal'
        formdata['giftdays'] = 0
        formdata['giftflows'] = 0
        formdata['ip_address'] = ''
        formdata['status'] = 1
        formdata['vcard_code'] = vcard_code
        formdata['vcard_pwd'] = vcard_pwd
        formdata['customer_desc'] = u'客户自助充值卡开户'
        formdata['product_name'] = product.product_name
        manager = CustomerAdd(self.db, self.aes)
        ret = manager.add(formdata)
        if ret:
            order = self.db.query(models.TrCustomerOrder).get(order_id)
            logger.info(u'充值卡开户成功')
            self.render('profile_alipay_return.html', order=order)
        else:
            return self.render_error(code=1, msg=u'充值卡订单处理失败 %s' % manager.last_error)

    def post(self):
        try:
            product_id = self.get_argument('product_id', '')
            product = self.db.query(models.TrProduct).get(product_id)
            if not product:
                return self.render('profile_neworder_form.html', form=form, msg=u'套餐不存在')
            form = order_forms.order_form(product.product_policy)
            if not form.validates(source=self.get_params()):
                return self.render('profile_neworder_form.html', form=form, msg=form.errors)
            account_count = self.db.query(models.TrCustomer).filter_by(email=form.d.email).count()
            if account_count > 0:
                return self.render('profile_neworder_form.html', form=form, msg=u'电子邮件已经存在')
            if form.d.vcard_code and form.d.vcard_pwd:
                return self.do_vcard(form, product)
            _feevalue, _expire = self.order_calc(form.d.product_id)
            order_id = utils.gen_order_id()
            formdata = Storage(form.d)
            formdata.order_id = order_id
            formdata['node_id'] = self.get_param_value('default_user_node_id', 1)
            formdata['area_id'] = ''
            formdata['fee_value'] = _feevalue
            formdata['expire_date'] = _expire
            formdata['accept_source'] = 'usrportal'
            formdata['giftdays'] = 0
            formdata['giftflows'] = 0
            formdata['ip_address'] = ''
            formdata['status'] = 1
            formdata['customer_desc'] = u'客户自助开户'
            formdata['product_name'] = product.product_name
            self.paycache.set(order_paycaache_key(order_id), formdata)
            return self.render('profile_order_alipay.html', formdata=formdata)
        except Exception as err:
            logger.exception(err)
            return self.render('profile_neworder_form.html', form=form, msg=u'无效的订单')


@permit.route('/usrportal/product/reneworder')

class UsrPortalProductOrderNewHandler(BasicOrderHandler):
    """  支付宝支付第一步：进入订购表单，发起订购支付
    """
    def get_expire_date(self, expire):
        if utils.is_expire(expire):
            return utils.get_currdate()
        else:
            return expire

    def get_product_name(self, pid):
        return self.db.query(models.TrProduct.product_name).filter_by(id=pid).scalar()

    def get(self):
        product_id = self.get_argument('product_id')
        product = self.db.query(models.TrProduct).get(product_id)
        get_product_attr_val = lambda an: self.db.query(models.TrProductAttr.attr_value).filter_by(product_id=product_id, attr_name=an).scalar()
        if not product:
            self.render_error(msg=u'套餐不存在')
            return
        account_number = self.current_user.username
        account = self.db.query(models.TrAccount).get(account_number)
        if not account_number or not account:
            self.render_error(msg=u'用户不存在')
            return

        form = order_forms.profile_order_form(product.product_policy, get_product_attr_val)
        form.product_id.set_value(product_id)
        form.product_name.set_value(product.product_name)
        form.months.set_value(product.fee_months)
        form.days.set_value(product.fee_days)
        form.account_number.set_value(account_number)
        self.render('profile_reneworder_form.html', form=form)

    def do_vcard(self, form, product):
        account = self.db.query(models.TrAccount).get(form.d.account_number)
        if not account:
            return self.render_json(code=1, msg=u'账号不存在')

        vcard_code = form.d.vcard_code
        vcard_pwd = form.d.vcard_pwd
        product_id = form.d.product_id
        _feevalue, _expire = self.order_calc(product_id)

        order_id = utils.gen_order_id()
        formdata = Storage(form.d)
        formdata['order_id'] = order_id
        formdata['product_id'] = product_id
        formdata['fee_value'] = _feevalue
        formdata['expire_date'] = _expire
        formdata['accept_source'] = 'usrportal'
        formdata['giftdays'] = 0
        formdata['giftflows'] = 0
        formdata['operate_desc'] = u'用户自助续费'
        formdata['old_expire'] = account.expire_date
        formdata['vcard_code'] = vcard_code
        formdata['vcard_pwd'] = vcard_pwd

        manager = AccountRenew(self.db, self.aes)
        ret = manager.renew(formdata)
        if ret:
            order = self.db.query(models.TrCustomerOrder).get(order_id)
            logger.info(u'充值卡续费成功')
            self.render('profile_alipay_return.html', order=order)
        else:
            return self.render('profile_reneworder_form.html', form=form, msg=u'%s' % manager.last_error)

    def post(self):

        product_id = self.get_argument('product_id', '')
        product = self.db.query(models.TrProduct).get(product_id)
        get_product_attr_val = lambda an: self.db.query(models.TrProductAttr.attr_value).filter_by(product_id=product_id, attr_name=an).scalar()
        if not product:
            self.render_error(msg=u'套餐不存在')
            return
        form = order_forms.profile_order_form(product.product_policy, get_product_attr_val)
        if not form.validates(source=self.get_params()):
            self.render_error(msg=form.errors)
            return

        account = self.db.query(models.TrAccount).get(form.d.account_number)
        if not account:
            self.render_error(msg=u'用户不存在')
            return

        if get_product_attr_val('product_tag') and form.d.vcard_code and form.d.vcard_pwd:
            return self.do_vcard(form, product)

        try:
            _feevalue, _expire = self.order_calc(form.d.product_id, old_expire=self.get_expire_date(account.expire_date))
            order_id = utils.gen_order_id()
            formdata = Storage(form.d)
            formdata.order_id = order_id
            formdata['product_id'] = product_id
            formdata['fee_value'] = _feevalue
            formdata['expire_date'] = _expire
            formdata['accept_source'] = 'usrportal'
            formdata['giftdays'] = 0
            formdata['giftflows'] = 0
            formdata['customer_desc'] = u'客户自助续费'
            formdata['old_expire'] = account.expire_date
            self.paycache.set(order_paycaache_key(order_id), formdata)
            return self.render('profile_renew_alipay.html', formdata=formdata)
        except Exception as err:
            logger.exception(err)
            return self.render('profile_reneworder_form.html', form=form, msg=u'无效的订单')

@permit.route('/usrportal/product/order/alipay')

class UsrPortalProductOrderHandler(BaseHandler):
    """ 支付宝支付第二步： 支付信息确认，跳转支付宝
    """

    def post(self):
        order_id = self.get_argument('order_id')
        formdata = self.paycache.get(order_paycaache_key(order_id))
        product_name = self.db.query(models.TrProduct.product_name).filter_by(id=formdata.product_id).scalar()
        self.redirect(self.alipay.create_direct_pay_by_user(order_id, product_name, product_name, formdata.fee_value, notify_path='/usrportal/alipay/verify/new', return_path='/usrportal/alipay/verify/new'))


@permit.route('/usrportal/sms/sendvcode')

class SendSmsVcodeHandler(BaseHandler):

    @defer.inlineCallbacks
    def get(self):
        yield self.post()

    @defer.inlineCallbacks
    def post(self):
        try:
            phone = self.get_argument('phone')
            last_send = self.session.get('sms_last_send', 0)
            if last_send > 0:
                sec = int(time.time()) - last_send
                if sec < 60:
                    self.render_json(code=1, msg=u'还需等待%s秒' % sec)
                    return
            self.session['sms_last_send'] = int(time.time())
            self.session.save()
            vcode = str(time.time()).replace('.', '')[-6:]
            self.cache.set('usrportal.sms.vcode.{}'.format(phone), vcode, expire=300)
            gateway = self.get_param_value('sms_gateway')
            apikey = self.get_param_value('sms_api_user')
            apisecret = self.get_param_value('sms_api_pwd')
            tplid = self.get_tpl_id(VcodeNotify)
            if not tplid:
                self.render_json(code=1, msg=u'没有对应的短信模版')
                return
            resp = yield smsapi.send_sms(gateway, apikey, apisecret, phone, tplid, args=[vcode], kwargs=dict(vcode=vcode))
            self.render_json(code=0, msg='ok')
        except Exception as err:
            logger.exception(err)
            self.render_json(code=1, msg=u'发送短信失败')