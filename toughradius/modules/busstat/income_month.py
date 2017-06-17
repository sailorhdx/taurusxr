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

@permit.suproute('/admin/stat/income/month', u'营业月统计', MenuStat, order=1.00002, is_menu=True)

class IncomeMonthStatHandler(BaseHandler):

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
        _query = self.db.query(models.TrCustomer.node_id, models.TrNode.node_name, models.TrCustomerOrder.product_id, models.TrProduct.product_name, models.TrAcceptLog.operator_name, func.sum(models.TrCustomerOrder.actual_fee).label('actual_fee'), func.count(models.TrCustomerOrder.order_id).label('dev_count'), models.TrCustomerOrder.stat_month).filter(models.TrCustomerOrder.product_id == models.TrProduct.id, models.TrCustomerOrder.customer_id == models.TrCustomer.customer_id, models.TrNode.id == models.TrCustomer.node_id, models.TrAcceptLog.id == models.TrCustomerOrder.accept_id)
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
            _query = _query.filter(models.TrCustomerOrder.stat_month >= query_begin_time)
        if query_end_time:
            _query = _query.filter(models.TrCustomerOrder.stat_month <= query_end_time)
        _query = _query.group_by('stat_month', 'node_id', 'node_name', 'product_id', 'product_name', 'operator_name')
        _query = _query.order_by('stat_month')
        userqry = _query.subquery()
        fee_total = self.db.query(func.sum(userqry.c.actual_fee)).scalar() or 0
        dev_total = self.db.query(func.sum(userqry.c.dev_count)).scalar() or 0
        if self.request.path == '/admin/stat/income/month':
            return self.render('income_month_stat.html', node_list=opr_nodes, fee_total=fee_total, dev_total=dev_total, products=opr_products, statitems=_query.limit(5000), **self.get_params())
        elif self.request.path == '/admin/stat/income/month/export':
            data = Dataset()
            data.append((u'月份', u'区域', u'资费', u'操作员', u'受理用户数', u'总金额'))
            _f2y = utils.fen2yuan
            for i in _query:
                data.append((i.stat_month,
                 i.node_name,
                 i.product_name,
                 i.operator_name,
                 i.dev_count,
                 _f2y(i.actual_fee)))

            name = u'RADIUS-INCOME-MONTH-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.xls'
            return self.export_file(name, data)
        else:
            return


@permit.suproute('/admin/stat/income/month/export', u'营业月统计导出', MenuStat, order=1.10001)

class IncomeMonthStatExportHandler(IncomeMonthStatHandler):
    pass


@permit.suproute('/admin/stat/income/trend/month', u'运营分析－营收月趋势', MenuStat, order=5.0001)

class IncomeMonthTrendHandler(BaseHandler):

    @authenticated
    def get(self):
        pay_status = self.get_argument('pay_status', None)
        accept_type = self.get_argument('accept_type', None)
        stat_month = self.get_argument('stat_month', utils.get_currdate()[0:7])
        _query = self.db.query(models.TrCustomerOrder.stat_day, func.sum(models.TrCustomerOrder.actual_fee).label('fee_value'), func.count(models.TrCustomerOrder.order_id).label('dev_count')).filter(models.TrCustomer.customer_id == models.TrCustomerOrder.customer_id, models.TrCustomerOrder.stat_month == stat_month, models.TrAcceptLog.id == models.TrCustomerOrder.accept_id)
        if pay_status:
            _query = _query.filter(models.TrCustomerOrder.pay_status == int(pay_status))
        if accept_type:
            _query = _query.filter(models.TrAcceptLog.accept_type == accept_type)
        _query = _query.group_by(models.TrCustomerOrder.stat_day)
        _query = _query.order_by(models.TrCustomerOrder.stat_day.asc())
        userqry = _query.subquery()
        fee_total = self.db.query(func.sum(userqry.c.fee_value)).scalar() or 0
        dev_total = self.db.query(func.sum(userqry.c.dev_count)).scalar() or 0
        fee_data = [ (i.stat_day, float(utils.fen2yuan(i.fee_value))) for i in _query ]
        dev_data = [ (i.stat_day, float(i.dev_count)) for i in _query ]
        categories = [ i.stat_day for i in _query ]
        self.render_json(code=0, msg='ok', fee_data=fee_data, dev_data=dev_data, categories=categories, dev_total=int(dev_total), fee_total=utils.fen2yuan(fee_total))
        return


@permit.suproute('/admin/stat/income/noderate/month', u'运营分析－区域营收比例(月)', MenuStat, order=5.0002)

class IncomeMonthNoderateHandler(BaseHandler):

    @authenticated
    def get(self):
        pay_status = self.get_argument('pay_status', None)
        accept_type = self.get_argument('accept_type', None)
        stat_month = self.get_argument('stat_month', utils.get_currdate()[0:7])
        _query = self.db.query(models.TrNode.node_name, func.sum(models.TrCustomerOrder.actual_fee).label('fee_value'), func.count(models.TrCustomerOrder.order_id).label('dev_count')).filter(models.TrCustomer.customer_id == models.TrCustomerOrder.customer_id, models.TrNode.id == models.TrCustomer.node_id, models.TrCustomerOrder.stat_month == stat_month)
        if pay_status:
            _query = _query.filter(models.TrCustomerOrder.pay_status == int(pay_status))
        if accept_type:
            _query = _query.filter(models.TrAcceptLog.accept_type == accept_type)
        _query = _query.group_by(models.TrNode.node_name)
        _query = _query.order_by(models.TrNode.node_name.asc())
        userqry = _query.subquery()
        fee_total = self.db.query(func.sum(userqry.c.fee_value)).scalar() or 0
        dev_total = self.db.query(func.sum(userqry.c.dev_count)).scalar() or 0
        fee_data = [ {'name': i.node_name,
         'y': float(utils.fen2yuan(i.fee_value))} for i in _query ]
        dev_data = [ {'name': i.node_name,
         'y': float(i.dev_count)} for i in _query ]
        self.render_json(code=0, msg='ok', fee_data=fee_data, dev_data=dev_data, dev_total=int(dev_total), fee_total=utils.fen2yuan(fee_total))
        return


@permit.suproute('/admin/stat/income/productrate/month', u'运营分析－资费营收比例(月)', MenuStat, order=5.0002)

class IncomeMonthProductRateHandler(BaseHandler):

    @authenticated
    def get(self):
        pay_status = self.get_argument('pay_status', None)
        accept_type = self.get_argument('accept_type', None)
        stat_month = self.get_argument('stat_month', utils.get_currdate()[0:7])
        _query = self.db.query(models.TrProduct.product_name, func.sum(models.TrCustomerOrder.actual_fee).label('fee_value'), func.count(models.TrCustomerOrder.order_id).label('dev_count')).filter(models.TrCustomer.customer_id == models.TrCustomerOrder.customer_id, models.TrProduct.id == models.TrCustomerOrder.product_id, models.TrCustomerOrder.stat_month == stat_month)
        if pay_status:
            _query = _query.filter(models.TrCustomerOrder.pay_status == int(pay_status))
        if accept_type:
            _query = _query.filter(models.TrAcceptLog.accept_type == accept_type)
        _query = _query.group_by(models.TrProduct.product_name)
        _query = _query.order_by(models.TrProduct.product_name.asc())
        userqry = _query.subquery()
        fee_total = self.db.query(func.sum(userqry.c.fee_value)).scalar() or 0
        dev_total = self.db.query(func.sum(userqry.c.dev_count)).scalar() or 0
        fee_data = [ {'name': i.product_name,
         'y': float(utils.fen2yuan(i.fee_value))} for i in _query ]
        dev_data = [ {'name': i.product_name,
         'y': float(i.dev_count)} for i in _query ]
        self.render_json(code=0, msg='ok', fee_data=fee_data, dev_data=dev_data, dev_total=int(dev_total), fee_total=utils.fen2yuan(fee_total))
        return

@permit.suproute('/admin/stat/income/oprrate/month', u'运营分析－操作员营收比例(月)', MenuStat, order=5.0003)

class IncomeMonthOprRateHandler(BaseHandler):

    @authenticated
    def get(self):
        pay_status = self.get_argument('pay_status', None)
        accept_type = self.get_argument('accept_type', None)
        stat_month = self.get_argument('stat_month', utils.get_currdate()[0:7])
        _query = self.db.query(models.TrAcceptLog.operator_name, func.sum(models.TrCustomerOrder.actual_fee).label('fee_value'), func.count(models.TrCustomerOrder.order_id).label('dev_count')).filter(models.TrCustomer.customer_id == models.TrCustomerOrder.customer_id, models.TrAcceptLog.id == models.TrCustomerOrder.accept_id, models.TrCustomerOrder.stat_month == stat_month)
        if pay_status:
            _query = _query.filter(models.TrCustomerOrder.pay_status == int(pay_status))
        if accept_type:
            _query = _query.filter(models.TrAcceptLog.accept_type == accept_type)
        _query = _query.group_by(models.TrAcceptLog.operator_name)
        _query = _query.order_by(models.TrAcceptLog.operator_name.asc())
        userqry = _query.subquery()
        fee_total = self.db.query(func.sum(userqry.c.fee_value)).scalar() or 0
        dev_total = self.db.query(func.sum(userqry.c.dev_count)).scalar() or 0
        fee_data = [ {'name': i.operator_name,
         'y': float(utils.fen2yuan(i.fee_value))} for i in _query ]
        dev_data = [ {'name': i.operator_name,
         'y': float(i.dev_count)} for i in _query ]
        self.render_json(code=0, msg='ok', fee_data=fee_data, dev_data=dev_data, dev_total=int(dev_total), fee_total=utils.fen2yuan(fee_total))
        return