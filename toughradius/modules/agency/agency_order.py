#!/usr/bin/env python
# coding=utf-8
from sqlalchemy import func
from hashlib import md5
from toughradius.toughlib import utils
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.agency import agency_form
from toughradius.modules.agency.agency_form import opr_status_dict
from toughradius.modules.settings import *
fee_types = {'recharge': u'余额充值',
 'share': u'收入分成',
 'sharecost': u'费用分摊',
 'cost': u'费用扣除'}

@permit.route('/admin/agency/orders', u'代理商交易查询', MenuAgency, order=2.0, is_menu=True)

class AgencyOrderHandler(BaseHandler):

    @authenticated
    def get(self):
        self.post()

    @authenticated
    def post(self):
        agency_id = self.get_argument('agency_id', '').strip() or self.current_user.agency_id
        fee_type = self.get_argument('fee_type', '')
        query_begin_time = self.get_argument('query_begin_time', None)
        query_end_time = self.get_argument('query_end_time', None)
        opr_agencies = self.get_opr_agencies()
        query = self.db.query(models.TrAgency.id, models.TrAgency.agency_name, models.TrAgencyOrder.fee_type, models.TrAgencyOrder.fee_value, models.TrAgencyOrder.fee_total, models.TrAgencyOrder.fee_desc, models.TrAgencyOrder.create_time).filter(models.TrAgency.id == models.TrAgencyOrder.agency_id)
        if agency_id:
            query = query.filter(models.TrAgency.id == agency_id)
        if fee_type:
            query = query.filter(models.TrAgencyOrder.fee_type == fee_type)
        if query_begin_time:
            query = query.filter(models.TrAgencyOrder.create_time >= query_begin_time + ' 00:00:00')
        if query_end_time:
            query = query.filter(models.TrAgencyOrder.create_time <= query_end_time + ' 23:59:59')
        query = query.order_by(models.TrAgencyOrder.create_time.desc())
        fee_value_sum = self.db.query(func.sum(query.subquery().c.fee_value)).scalar()
        self.render('agency_orders.html', orders=query.limit(3000), fee_value_sum=fee_value_sum, opr_agencies=opr_agencies, fee_types=fee_types, **self.get_params())
        return