#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
from tablib import Dataset
from toughradius.modules import models
from toughradius.modules.ssportal.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules.settings import *

@permit.route('/ssportal/order')

class OrderHandler(BaseHandler):

    @authenticated
    def get(self):
        self.post()

    @authenticated
    def post(self):
        query_begin_time = self.get_argument('query_begin_time', None)
        query_end_time = self.get_argument('query_end_time', None)
        _query = self.db.query(models.TrCustomerOrder, models.TrCustomer.node_id, models.TrCustomer.realname, models.TrProduct.product_name, models.TrNode.node_name, models.TrCharges.charge_name, models.TrCharges.charge_value).outerjoin(models.TrChargeLog, models.TrCustomerOrder.order_id == models.TrChargeLog.order_id).outerjoin(models.TrCharges, models.TrChargeLog.charge_code == models.TrCharges.charge_code).filter(models.TrCustomerOrder.product_id == models.TrProduct.id, models.TrCustomerOrder.customer_id == models.TrCustomer.customer_id, models.TrNode.id == models.TrCustomer.node_id, models.TrCustomerOrder.account_number == self.current_user.username)
        if query_begin_time:
            _query = _query.filter(models.TrCustomerOrder.create_time >= query_begin_time + ' 00:00:00')
        if query_end_time:
            _query = _query.filter(models.TrCustomerOrder.create_time <= query_end_time + ' 23:59:59')
        _query = _query.order_by(models.TrCustomerOrder.create_time.desc())
        return self.render('order_list.html', page_data=self.get_page_data(_query, page_size=100), **self.get_params())