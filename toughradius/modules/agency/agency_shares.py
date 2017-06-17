#!/usr/bin/env python
# coding=utf-8
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
from toughradius.modules.settings import *

@permit.route('/admin/agency/shares', u'代理分成查询', MenuAgency, order=3.0, is_menu=True)

class AgencySharesHandler(CustomerHandler):

    @authenticated
    def get(self):
        self.post()

    @authenticated
    def post(self):
        node_id = self.get_argument('node_id', None)
        agency_id = self.get_argument('agency_id', '').strip() or self.current_user.agency_id
        product_id = self.get_argument('product_id', None)
        query_begin_time = self.get_argument('query_begin_time', None)
        query_end_time = self.get_argument('query_end_time', None)
        pay_status = self.get_argument('pay_status', None)
        opr_nodes = self.get_opr_nodes()
        opr_agencies = self.get_opr_agencies()
        _query = self.db.query(models.TrCustomer.node_id, models.TrNode.node_name, models.TrCustomerOrder.product_id, models.TrProduct.product_name, models.TrAgencyShare.agency_id, models.TrAgency.agency_name, func.sum(models.TrCustomerOrder.actual_fee).label('actual_fee'), func.sum(models.TrAgencyShare.share_fee).label('share_fee'), models.TrCustomerOrder.stat_day).filter(models.TrCustomerOrder.product_id == models.TrProduct.id, models.TrCustomerOrder.customer_id == models.TrCustomer.customer_id, models.TrCustomerOrder.order_id == models.TrAgencyShare.order_id, models.TrAgency.id == models.TrAgencyShare.agency_id, models.TrNode.id == models.TrCustomer.node_id)
        if node_id:
            _query = _query.filter(models.TrCustomer.node_id == node_id)
        else:
            _query = _query.filter(models.TrCustomer.node_id.in_([ i.id for i in opr_nodes ]))
        if agency_id:
            _query = _query.filter(models.TrAgencyShare.agency_id == agency_id)
        if pay_status:
            _query = _query.filter(models.TrCustomerOrder.pay_status == int(pay_status))
        if product_id:
            _query = _query.filter(models.TrCustomerOrder.product_id == product_id)
        if query_begin_time:
            _query = _query.filter(models.TrCustomerOrder.create_time >= query_begin_time + ' 00:00:00')
        if query_end_time:
            _query = _query.filter(models.TrCustomerOrder.create_time <= query_end_time + ' 23:59:59')
        _query = _query.group_by('stat_day', 'node_id', 'node_name', 'product_id', 'product_name', 'agency_id', 'agency_name')
        _query = _query.order_by('stat_day')
        userqry = _query.subquery()
        fee_totals = self.db.query(func.sum(userqry.c.actual_fee), func.sum(userqry.c.share_fee)).first() or (0, 0)
        if self.request.path == '/admin/agency/shares':
            return self.render('agency_shares.html', node_list=opr_nodes, opr_agencies=opr_agencies, fee_totals=fee_totals, products=self.db.query(models.TrProduct), shares=_query.limit(3000), **self.get_params())
        elif self.request.path == '/admin/agency/shares/export':
            data = Dataset()
            data.append((u'日期', u'区域', u'代理商', u'资费', u'总金额', u'分成总额'))
            _f2y = utils.fen2yuan
            for i in _query:
                data.append((i.stat_day,
                 i.node_name,
                 i.agency_name,
                 i.product_name,
                 _f2y(i.actual_fee),
                 _f2y(i.share_fee)))

            name = u'RADIUS-AGENCYFEE-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.xls'
            return self.export_file(name, data)
        else:
            return


@permit.route('/admin/agency/shares/export', u'代理分成统计导出', MenuAgency, order=2.000001)

class AgencySharesExportHandler(AgencySharesHandler):
    pass