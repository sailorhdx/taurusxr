#!/usr/bin/env python
# coding=utf-8
import datetime
import time
from toughradius.modules.ssportal.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.toughlib import utils, dispatch, db_cache
from toughradius.common import tools
from toughradius.modules.settings import *

@permit.route('/ssportal/account')

class AccountHandler(BaseHandler):

    @authenticated
    def get(self):
        account_number = self.current_user.username
        user = self.db.query(models.TrCustomer.realname, models.TrNode.node_name, models.TrArea.area_name, models.TrAccount.customer_id, models.TrAccount.account_number, models.TrAccount.password, models.TrAccount.expire_date, models.TrAccount.balance, models.TrAccount.time_length, models.TrAccount.flow_length, models.TrAccount.user_concur_number, models.TrAccount.status, models.TrAccount.mac_addr, models.TrAccount.vlan_id1, models.TrAccount.vlan_id2, models.TrAccount.ip_address, models.TrAccount.bind_mac, models.TrAccount.bind_vlan, models.TrAccount.ip_address, models.TrAccount.install_address, models.TrAccount.last_pause, models.TrAccount.create_time, models.TrProduct.product_name, models.TrProduct.product_policy).outerjoin(models.TrArea, models.TrCustomer.area_id == models.TrArea.id).filter(models.TrProduct.id == models.TrAccount.product_id, models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrCustomer.node_id == models.TrNode.id, models.TrAccount.account_number == account_number).first()
        customer = self.db.query(models.TrCustomer).get(user.customer_id)
        orders = self.db.query(models.TrCustomerOrder, models.TrCustomer.realname, models.TrProduct.product_name).filter(models.TrCustomerOrder.product_id == models.TrProduct.id, models.TrCustomerOrder.customer_id == models.TrCustomer.customer_id, models.TrCustomerOrder.account_number == self.current_user.username, models.TrCustomerOrder.pay_status == 0)
        type_map = ACCEPT_TYPES
        get_attr_val = lambda an: self.db.query(models.TrAccountAttr.attr_value).filter_by(account_number=self.current_user.username, attr_name=an).scalar()
        return self.render('account.html', customer=customer, user=user, orders=orders, get_attr_val=get_attr_val, type_map=type_map)


@permit.route('/ssportal/account/release')

class AccountReleasetHandler(BaseHandler):

    @authenticated
    def post(self):
        account_number = self.current_user.username
        user = self.db.query(models.TrAccount).filter_by(account_number=account_number).first()
        user.mac_addr = ''
        user.vlan_id1 = 0
        user.vlan_id2 = 0
        user.sync_ver = tools.gen_sync_ver()
        self.db.commit()
        dispatch.pub(db_cache.CACHE_DELETE_EVENT, account_cache_key(account_number), async=True)
        return self.render_json(msg=u'解绑成功')