#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
from sqlalchemy import func
from tablib import Dataset
from toughradius.modules import models
from toughradius.modules.customer import customer_forms
from toughradius.modules.base import authenticated
from toughradius.modules.customer.customer import CustomerHandler
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.common import tools
from toughradius.modules.settings import *

@permit.route('/admin/customer/order', u'用户交易管理', MenuUser, order=1.5, is_menu=True)

class CustomerOrderHandler(CustomerHandler):

    @authenticated
    def get(self):
        self.post()

    @authenticated
    def post(self):
        node_id = self.get_argument('node_id', None)
        product_id = self.get_argument('product_id', None)
        pay_status = self.get_argument('pay_status', None)
        account_number = self.get_argument('account_number', None)
        query_begin_time = self.get_argument('query_begin_time', None)
        query_end_time = self.get_argument('query_end_time', None)
        page_size = int(self.get_argument('page_size', 10))
        agency_id = self.get_argument('agency_id', '').strip() or self.current_user.agency_id
        opr_nodes = self.get_opr_nodes()
        opr_agencies = self.get_opr_agencies()
        _query = self.db.query(models.TrCustomerOrder.order_id, models.TrCustomerOrder.account_number, models.TrCustomerOrder.pay_status, models.TrCustomerOrder.order_fee, models.TrCustomerOrder.actual_fee, models.TrCustomerOrder.create_time, models.TrCustomerOrder.order_source, models.TrCustomerOrder.order_desc, models.TrCustomer.node_id, models.TrCustomer.realname, models.TrAccount.status, models.TrAccount.create_time.label('begin_time'), models.TrAccount.expire_date, models.TrProduct.product_name, models.TrNode.node_name).filter(models.TrCustomerOrder.product_id == models.TrProduct.id, models.TrCustomerOrder.customer_id == models.TrCustomer.customer_id, models.TrCustomerOrder.customer_id == models.TrAccount.customer_id, models.TrNode.id == models.TrCustomer.node_id)
        if node_id:
            _query = _query.filter(models.TrCustomer.node_id == node_id)
        else:
            _query = _query.filter(models.TrCustomer.node_id.in_([ i.id for i in opr_nodes ]))
        if agency_id:
            _query = _query.filter(models.TrCustomer.agency_id == agency_id)
        if account_number:
            _query = _query.filter(models.TrCustomerOrder.account_number.like('%' + account_number + '%'))
        if product_id:
            _query = _query.filter(models.TrCustomerOrder.product_id == product_id)
        if pay_status:
            _query = _query.filter(models.TrCustomerOrder.pay_status == pay_status)
        if query_begin_time:
            _query = _query.filter(models.TrCustomerOrder.create_time >= query_begin_time + ' 00:00:00')
        if query_end_time:
            _query = _query.filter(models.TrCustomerOrder.create_time <= query_end_time + ' 23:59:59')
        _query = _query.order_by(models.TrCustomerOrder.create_time.desc())
        userqry = _query.subquery()
        fee_totals = self.db.query(func.sum(userqry.c.order_fee), func.sum(userqry.c.actual_fee)).first() or (0, 0)
        if self.request.path == '/admin/customer/order':
            return self.render('order_list.html', node_list=opr_nodes, opr_agencies=opr_agencies, fee_totals=fee_totals, products=self.get_opr_products(), page_data=self.get_page_data(_query, page_size), **self.get_params())
        elif self.request.path == '/admin/customer/order/export':
            data = Dataset()
            data.append((u'区域', u'用户姓名', u'上网账号', u'状态', u'开户时间', u'过期时间', u'资费', u'交易时间', u'订单金额', u'实缴金额', u'交易状态', u'订购渠道', u'订单描述'))
            _f2y = utils.fen2yuan
            _fms = utils.fmt_second
            _pst = {OUnPay: u'未支付',
             OPaid: u'已支付',
             OChecked: u'已对账'}
            _ustate = {UsrPreAuth: u'未激活',
             UsrNormal: u'正常',
             UsrPause: u'停机',
             UsrCancel: u'销户',
             UsrExpire: u'到期'}
            for i in _query:
                data.append((i.node_name,
                 i.realname,
                 i.account_number,
                 _ustate.get(i.status),
                 i.begin_time[0:10],
                 i.expire_date,
                 i.product_name,
                 i.create_time,
                 _f2y(i.order_fee),
                 _f2y(i.actual_fee),
                 _pst.get(i.pay_status),
                 i.order_source,
                 i.order_desc))

            name = u'RADIUS-ORDERS-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.xls'
            return self.export_file(name, data)
        else:
            return


@permit.route('/admin/customer/order/export', u'用户交易日志导出', MenuUser, order=1.500001)

class CustomerOrderExportHandler(CustomerOrderHandler):
    pass


@permit.route('/admin/customer/order/check', u'用户交易对账', MenuUser, order=1.500002, is_menu=False)

class CustomerOrderAuditHandler(CustomerHandler):

    @authenticated
    def get(self):
        order_id = self.get_argument('order_id')
        form = customer_forms.customer_order_check_form()
        order = self.db.query(models.TrCustomerOrder).get(order_id)
        form.order_id.set_value(order_id)
        form.order_fee.set_value(utils.fen2yuan(order.order_fee))
        form.actual_fee.set_value(utils.fen2yuan(order.actual_fee))
        return self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = customer_forms.customer_order_check_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        audit_desc = utils.safeunicode(form.d.audit_desc)
        order = self.db.query(models.TrCustomerOrder).get(form.d.order_id)
        new_actual_fee = utils.yuan2fen(form.d.actual_fee)
        if order.actual_fee != new_actual_fee:
            audit_desc += u'；调整费用 \xa5{} 为 \xa5{}'.format(utils.fen2yuan(order.actual_fee), form.d.actual_fee)
        checktime = utils.get_currtime()
        order.actual_fee = new_actual_fee
        order.pay_status = 2
        order.check_time = checktime
        order.order_desc += u'; 对账审核时间:{}'.format(checktime)
        audit_desc += u'; 订单ID:{}'.format(order.order_id)
        order.stat_year = order.create_time[0:4]
        order.stat_month = order.create_time[0:7]
        order.stat_day = order.create_time[0:10]
        self.add_oplog(audit_desc)
        self.db.commit()
        self.redirect('/admin/customer/order')


@permit.route('/admin/customer/order/bcheck', u'用户交易批量对账', MenuUser, order=1.500003, is_menu=False)

class CustomerOrderBAuditHandler(CustomerHandler):

    @authenticated
    def post(self):
        try:
            order_ids = self.get_argument('order_ids', '')
            idarray = [ p for p in order_ids.split(',') if p ]
            if not idarray:
                return self.render_json(code=1, msg=u'没有需要对账的交易记录')
            _query = self.db.query(models.TrCustomerOrder).filter(models.TrCustomerOrder.order_id.in_(idarray))
            total = 0
            for od in _query:
                if od.pay_status in (0, 1):
                    od.sync_ver = tools.gen_sync_ver()
                    od.pay_status = 2
                    od.check_time = utils.get_currtime()
                    od.order_desc += u'; 对账审核时间:{}'.format(od.check_time)
                    total += 1

            self.add_oplog(u'批量对账操作总数：%s' % total)
            self.db.commit()
            self.render_json(msg=u'操作成功')
        except Exception as err:
            self.render_json(code=1, msg=u'操作失败 %s' % err.message)