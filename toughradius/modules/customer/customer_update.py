#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
from hashlib import md5
from toughradius.modules import models
from toughradius.modules.base import authenticated
from toughradius.modules.customer import customer_forms
from toughradius.modules.customer.customer import CustomerHandler
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules.settings import *
from toughradius.common import tools

@permit.route('/admin/customer/update', u'用户修改', MenuUser, order=1.4)

class CustomerUpdateHandler(CustomerHandler):

    @authenticated
    def get(self):
        customer_id = self.get_argument('customer_id')
        account_number = self.get_argument('account_number')
        customer = self.db.query(models.TrCustomer).get(customer_id)
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        form = customer_forms.customer_update_form(nodes)
        form.fill(customer)
        form.account_number.set_value(account_number)
        return self.render('customer_update_form.html', form=form, customer=customer)

    @authenticated
    def post(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        form = customer_forms.customer_update_form(nodes)
        if not form.validates(source=self.get_params()):
            return self.render('customer_update_form.html', form=form)
        customer = self.db.query(models.TrCustomer).get(form.d.customer_id)
        customer.realname = form.d.realname
        if form.d.new_password:
            customer.password = md5(form.d.new_password.encode()).hexdigest()
        customer.node_id = form.d.node_id
        customer.area_id = form.d.area_id
        customer.email = form.d.email
        customer.idcard = form.d.idcard
        customer.mobile = form.d.mobile
        customer.address = form.d.address
        customer.customer_desc = form.d.customer_desc
        customer.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'修改用户信息 %s' % customer.customer_name)
        self.db.commit()
        self.redirect(self.detail_url_fmt(form.d.account_number))