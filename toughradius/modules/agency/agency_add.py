#!/usr/bin/env python
# coding=utf-8
from hashlib import md5
from toughradius.toughlib import utils
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.agency import agency_form
from toughradius.modules.agency.agency_form import opr_status_dict
from toughradius.modules.settings import *
from toughradius.modules.dbservice.agency_service import AgencyService

@permit.suproute('/admin/agency/add', u'代理商开户', MenuAgency, order=1.0001, is_menu=True)

class AddHandler(BaseHandler):

    @authenticated
    def get(self):
        nodes = [ (n.id, n.node_desc) for n in self.get_opr_nodes() ]
        products = [ (p.id, p.product_name) for p in self.get_opr_products() ]
        self.render('agency_form.html', form=agency_form.agency_add_form(nodes, products), rules=[])

    @authenticated
    def post(self):
        nodes = [ (n.id, n.node_desc) for n in self.get_opr_nodes() ]
        products = [ (p.id, p.product_name) for p in self.get_opr_products() ]
        rules = self.get_arguments('rule_item')
        form = agency_form.agency_add_form(nodes, products)
        if not form.validates(source=self.get_params()):
            return self.render('agency_form.html', form=form, rules=rules)
        manager = AgencyService(self.db, self.aes, operator=self.current_user)
        agency = manager.add(form.d, **dict(operator_nodes=self.get_arguments('operator_nodes'), operator_products=self.get_arguments('operator_products'), rule_item=self.get_arguments('rule_item')))
        if not agency:
            return self.render('agency_form.html', form=form, rules=rules, msg=manager.last_error)
        self.redirect('/admin/agency', permanent=False)