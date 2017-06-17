#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.toughlib import logger
from toughradius.toughlib import utils
from toughradius.toughlib.permit import permit
from toughradius.modules.mps.base import BaseHandler
from twisted.internet import defer
from toughradius.modules import models
from urllib import urlencode
from toughradius.common import tools
import base64

@permit.route('/mps/userorder')

class MpsUserOrderHandler(BaseHandler):

    def get(self):
        openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
        if not openid:
            cbk_param = urlencode({'cbk': '/mps/userorder'})
            return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
        customer = self.db.query(models.TrCustomer).filter_by(wechat_oid=openid).first()
        if not customer:
            return self.redirect('/mps/userbind', permanent=False)
        orders = self.db.query(models.TrCustomerOrder.order_id, models.TrCustomerOrder.account_number, models.TrCustomerOrder.pay_status, models.TrCustomerOrder.actual_fee, models.TrCustomerOrder.create_time, models.TrCustomerOrder.order_source, models.TrCustomerOrder.order_desc, models.TrCustomer.realname, models.TrProduct.product_name).filter(models.TrCustomerOrder.product_id == models.TrProduct.id, models.TrCustomerOrder.customer_id == models.TrCustomer.customer_id, models.TrCustomer.wechat_oid == openid).limit(20)
        self.render('userorder.html', orders=orders)