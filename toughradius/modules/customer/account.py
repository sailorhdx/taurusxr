#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.customer import account_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules.settings import *

class AccountHandler(BaseHandler):
    detail_url_fmt = '/admin/customer/detail?account_number={0}'.format

    def query_account(self, account_number):
        return self.db.query(models.TrCustomer.realname, models.TrAccount.customer_id, models.TrAccount.product_id, models.TrAccount.account_number, models.TrAccount.expire_date, models.TrAccount.balance, models.TrAccount.time_length, models.TrAccount.flow_length, models.TrAccount.user_concur_number, models.TrAccount.status, models.TrAccount.mac_addr, models.TrAccount.vlan_id1, models.TrAccount.vlan_id2, models.TrAccount.ip_address, models.TrAccount.bind_mac, models.TrAccount.bind_vlan, models.TrAccount.ip_address, models.TrAccount.install_address, models.TrAccount.create_time, models.TrProduct.product_name).filter(models.TrProduct.id == models.TrAccount.product_id, models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.account_number == account_number).first()


@permit.route('/admin/account/opencalc')

class OpencalcHandler(AccountHandler):

    @authenticated
    def post(self):
        months = int(self.get_argument('months', 0))
        days = int(self.get_argument('days', 0))
        product_id = self.get_argument('product_id', '')
        old_expire = self.get_argument('old_expire', '')
        giftdays = int(self.get_argument('giftdays', 0))
        product = self.db.query(models.TrProduct).get(product_id)
        charge_code = self.get_argument('charge_code', '')
        charge_value = 0
        if charge_code:
            charge_value = self.db.query(models.TrCharges).get(charge_code).charge_value
        if product.product_policy in (BOTimes, BOFlows):
            fee_value = utils.fen2yuan(product.fee_price + charge_value)
            return self.render_json(code=0, data=dict(policy=product.product_policy, fee_value=fee_value, expire_date=MAX_EXPIRE_DATE))
        if product.product_policy == PPMonth:
            fee = decimal.Decimal(months) * decimal.Decimal(product.fee_price)
            fee_value = utils.fen2yuan(int(fee.to_integral_value()) + charge_value)
            start_expire = datetime.datetime.now()
            if old_expire:
                start_expire = datetime.datetime.strptime(old_expire, '%Y-%m-%d')
            expire_date = utils.add_months(start_expire, int(months), days=giftdays)
            expire_date = expire_date.strftime('%Y-%m-%d')
            return self.render_json(code=0, data=dict(policy=product.product_policy, fee_value=fee_value, expire_date=expire_date))
        if product.product_policy == PPDay:
            fee = decimal.Decimal(days) * decimal.Decimal(product.fee_price)
            fee_value = utils.fen2yuan(int(fee.to_integral_value()) + charge_value)
            start_expire = datetime.datetime.now()
            if old_expire:
                start_expire = datetime.datetime.strptime(old_expire, '%Y-%m-%d')
            expire_date = start_expire + datetime.timedelta(days=days)
            expire_date = expire_date.strftime('%Y-%m-%d')
            return self.render_json(code=0, data=dict(policy=product.product_policy, fee_value=fee_value, expire_date=expire_date))
        if product.product_policy == APMonth:
            fee = decimal.Decimal(months) * decimal.Decimal(product.fee_price)
            fee_value = utils.fen2yuan(charge_value)
            return self.render_json(code=0, data=dict(policy=product.product_policy, fee_value=fee_value, expire_date=MAX_EXPIRE_DATE))
        if product.product_policy == BOMonth:
            start_expire = datetime.datetime.now()
            if old_expire:
                start_expire = datetime.datetime.strptime(old_expire, '%Y-%m-%d')
            fee_value = utils.fen2yuan(product.fee_price + charge_value)
            expire_date = utils.add_months(start_expire, product.fee_months, days=giftdays)
            expire_date = expire_date.strftime('%Y-%m-%d')
            return self.render_json(code=0, data=dict(policy=product.product_policy, fee_value=fee_value, expire_date=expire_date))
        if product.product_policy == BODay:
            start_expire = datetime.datetime.now()
            if old_expire:
                start_expire = datetime.datetime.strptime(old_expire, '%Y-%m-%d')
            fee_value = utils.fen2yuan(product.fee_price + charge_value)
            expire_date = start_expire + datetime.timedelta(days=product.fee_days + giftdays)
            expire_date = expire_date.strftime('%Y-%m-%d')
            return self.render_json(code=0, data=dict(policy=product.product_policy, fee_value=fee_value, expire_date=expire_date))
