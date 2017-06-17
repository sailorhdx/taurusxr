#!/usr/bin/env python
# coding=utf-8
import decimal
import datetime
from sqlalchemy import func
from tablib import Dataset
from toughradius.modules import models
from toughradius.modules.customer import customer_forms
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules.settings import *

@permit.suproute('/admin/stat/income/year', u'营业年统计', MenuStat, order=1.10003, is_menu=True)

class IncomeYearStatHandler(BaseHandler):

    @authenticated
    def get(self):
        self.post()

    @authenticated
    def post(self):
        node_id = self.get_argument('node_id', None)
        product_id = self.get_argument('product_id', None)
        operator_name = self.get_argument('operator_name', None)
        query_begin_time = self.get_argument('query_begin_time', None)
        query_end_time = self.get_argument('query_end_time', None)
        pay_status = self.get_argument('pay_status', None)
        accept_type = self.get_argument('accept_type', None)
        opr_nodes = self.get_opr_nodes()
        opr_products = self.get_opr_products()
        _query = self.db.query(models.TrCustomer.node_id, models.TrNode.node_name, models.TrCustomerOrder.product_id, models.TrProduct.product_name, models.TrAcceptLog.operator_name, func.sum(models.TrCustomerOrder.actual_fee).label('actual_fee'), func.count(models.TrCustomerOrder.order_id).label('dev_count'), models.TrCustomerOrder.stat_year).filter(models.TrCustomerOrder.product_id == models.TrProduct.id, models.TrCustomerOrder.customer_id == models.TrCustomer.customer_id, models.TrNode.id == models.TrCustomer.node_id, models.TrAcceptLog.id == models.TrCustomerOrder.accept_id)
        if node_id:
            _query = _query.filter(models.TrCustomer.node_id == node_id)
        else:
            _query = _query.filter(models.TrCustomer.node_id.in_([ i.id for i in opr_nodes ]))
        if pay_status:
            _query = _query.filter(models.TrCustomerOrder.pay_status == int(pay_status))
        if accept_type:
            _query = _query.filter(models.TrAcceptLog.accept_type == accept_type)
        if product_id:
            _query = _query.filter(models.TrCustomerOrder.product_id == product_id)
        if operator_name:
            _query = _query.filter(models.TrAcceptLog.operator_name == operator_name)
        if query_begin_time:
            _query = _query.filter(models.TrCustomerOrder.stat_year >= query_begin_time)
        if query_end_time:
            _query = _query.filter(models.TrCustomerOrder.stat_year <= query_end_time)
        _query = _query.group_by('stat_year', 'node_id', 'node_name', 'product_id', 'product_name', 'operator_name')
        _query = _query.order_by('stat_year')
        userqry = _query.subquery()
        fee_total = self.db.query(func.sum(userqry.c.actual_fee)).scalar() or 0
        dev_total = self.db.query(func.sum(userqry.c.dev_count)).scalar() or 0
        if self.request.path == '/admin/stat/income/year':
            return self.render('income_year_stat.html', node_list=opr_nodes, fee_total=fee_total, dev_total=dev_total, products=opr_products, statitems=_query.limit(5000), **self.get_params())
        elif self.request.path == '/admin/stat/income/year/export':
            data = Dataset()
            data.append((u'年份', u'区域', u'资费', u'操作员', u'受理用户数', u'总金额'))
            _f2y = utils.fen2yuan
            for i in _query:
                data.append((i.stat_year,
                 i.node_name,
                 i.product_name,
                 i.operator_name,
                 i.dev_count,
                 _f2y(i.actual_fee)))

            name = u'RADIUS-INCOME-YEAR-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.xls'
            return self.export_file(name, data)
        else:
            return


@permit.suproute('/admin/stat/income/year/export', u'营业年统计导出', MenuStat, order=1.10001)

class IncomeYearStatExportHandler(IncomeYearStatHandler):
    pass