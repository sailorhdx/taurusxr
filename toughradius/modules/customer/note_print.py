#!/usr/bin/env python
# coding=utf-8
import os
import json
import cyclone.web
import decimal
import datetime
from hashlib import md5
from toughradius.modules import models
from toughradius.modules.base import authenticated
from toughradius.modules.customer import note_forms
from toughradius.modules.customer.customer import CustomerHandler
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules.settings import *
from toughradius.common import tools
if os.environ.get('LICENSE_TYPE') != 'community':

    @permit.route('/admin/customer/note/getprint', u'用户票据打印', MenuUser, order=99.0, is_menu=False)

    class PrintFunctionGetHandler(CustomerHandler):

        @authenticated
        def post(self):
            order_id = self.get_argument('order_id')
            tpl_id = self.get_argument('tpl_id')
            tpl = self.db.query(models.TrPrintTemplate).get(tpl_id)
            note = self.db.query(models.TrCustomerNote).filter_by(order_id=order_id).first()
            print_params = dict(title=u'宽带票据', note_id=note.note_id, pay_type=note.pay_type, pay_date=note.pay_date, expire_date=note.expire_date, customer_name=note.customer_cname, install_address=note.install_address, product_name=note.product_name, product_price=utils.fen2yuan(note.fee_price), remark=note.remark, account_number=note.account_number, mobile=note.mobile, product_num=note.order_num, fee_total=utils.fen2yuan(note.fee_total), charge_values=utils.safeunicode(note.charge_values), receiver=note.operator_name, customer_sign='')
            print_func = tpl.tpl_content.format(**print_params)
            self.render_json(func=print_func)


    @permit.route('/admin/customer/note/print', u'用户票据打印', MenuUser, order=99.0, is_menu=False)

    class CustomerNotePrintHandler(CustomerHandler):

        def add_note(self, order_id):
            order = self.db.query(models.TrCustomerOrder).get(order_id)
            account = self.db.query(models.TrAccount).filter_by(account_number=order.account_number).first()
            product = self.db.query(models.TrProduct).filter_by(id=order.product_id).first()
            customer = self.db.query(models.TrCustomer).get(order.customer_id)
            opr = self.db.query(models.TrOperator).filter(models.TrCustomerOrder.accept_id == models.TrAcceptLog.id, models.TrAcceptLog.operator_name == models.TrOperator.operator_name, models.TrCustomerOrder.order_id == order_id).first()
            clogs = self.db.query(models.TrCharges.charge_name, models.TrCharges.charge_value).filter(models.TrCharges.charge_code == models.TrChargeLog.charge_code, models.TrChargeLog.order_id == order_id)
            charge_values = ', '.join([ '%s:%s' % (cname, utils.fen2yuan(cvalue)) for cname, cvalue in clogs ])
            note = models.TrCustomerNote()
            note.id = utils.get_uuid()
            note.note_id = utils.gen_order_id()
            note.order_id = order.order_id
            note.customer_cname = customer.realname
            note.account_number = account.account_number
            note.mobile = customer.mobile
            note.install_address = account.install_address
            note.pay_type = u'现金'
            note.pay_date = utils.get_currdate()
            note.expire_date = account.expire_date
            note.order_num = 1
            note.product_name = product.product_name
            note.fee_price = product.fee_price
            note.fee_total = order.actual_fee
            note.charge_values = charge_values
            note.operator_name = opr and opr.operator_desc or ''
            note.print_times = 0
            note.remark = u'用户套餐续费'
            note.sync_ver = tools.gen_sync_ver()
            self.db.add(note)
            self.db.commit()
            return note

        @authenticated
        def get(self):
            order_id = self.get_argument('order_id')
            note = self.db.query(models.TrCustomerNote).filter_by(order_id=order_id).first()
            if not note:
                note = self.add_note(order_id)
            tpl_query = self.db.query(models.TrPrintTemplate).filter(models.TrCustomerOrder.order_id == order_id, models.TrAcceptLog.id == models.TrCustomerOrder.accept_id, models.TrPrintTemplate.id == models.TrPrintTemplateTypes.tpl_id, models.TrAcceptLog.accept_type == models.TrPrintTemplateTypes.tpl_type)
            tpls = [ (tpl.id, tpl.tpl_name) for tpl in tpl_query ]
            self.render('note_print_form.html', note=note, tpls=tpls)

        @authenticated
        def post(self):
            order_id = self.get_argument('order_id')
            note = self.db.query(models.TrCustomerNote).filter_by(order_id=order_id).first()
            note.print_times = note.print_times + 1
            note.sync_ver = tools.gen_sync_ver()
            self.add_oplog(u'打印票据:%s' % note.note_id)
            self.db.commit()
            self.render_json(code=0)