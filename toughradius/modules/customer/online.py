#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules.settings import *

@permit.route('/admin/customer/online', u'用户在线查询', MenuUser, order=4.0, is_menu=True)

class CustomerOnlineHandler(BaseHandler):

    @authenticated
    def get(self):
        self.post()

    @authenticated
    def post(self):
        node_id = self.get_argument('node_id', None)
        account_number = self.get_argument('account_number', None)
        framed_ipaddr = self.get_argument('framed_ipaddr', None)
        agency_id = self.get_argument('agency_id', '').strip() or self.current_user.agency_id
        mac_addr = self.get_argument('mac_addr', None)
        nas_addr = self.get_argument('nas_addr', None)
        opr_nodes = self.get_opr_nodes()
        opr_agencies = self.get_opr_agencies()
        _query = self.db.query(models.TrOnline.id, models.TrOnline.account_number, models.TrOnline.nas_addr, models.TrOnline.acct_session_id, models.TrOnline.acct_start_time, models.TrOnline.framed_ipaddr, models.TrOnline.mac_addr, models.TrOnline.nas_port_id, models.TrOnline.start_source, models.TrOnline.billing_times, models.TrOnline.input_total, models.TrOnline.output_total, models.TrCustomer.node_id, models.TrCustomer.realname).filter(models.TrOnline.account_number == models.TrAccount.account_number, models.TrCustomer.customer_id == models.TrAccount.customer_id)
        if node_id:
            _query = _query.filter(models.TrCustomer.node_id == node_id)
        else:
            _query = _query.filter(models.TrCustomer.node_id.in_([ i.id for i in opr_nodes ]))
        if agency_id:
            _query = _query.filter(models.TrCustomer.agency_id == agency_id)
        if account_number:
            _query = _query.filter(models.TrOnline.account_number.like('%' + account_number + '%'))
        if framed_ipaddr:
            _query = _query.filter(models.TrOnline.framed_ipaddr == framed_ipaddr)
        if mac_addr:
            _query = _query.filter(models.TrOnline.mac_addr == mac_addr)
        if nas_addr:
            _query = _query.filter(models.TrOnline.nas_addr == nas_addr)
        _query = _query.order_by(models.TrOnline.acct_start_time.desc())
        return self.render('online_list.html', page_data=self.get_page_data(_query), node_list=opr_nodes, agency_list=opr_agencies, bas_list=self.db.query(models.TrBas), **self.get_params())