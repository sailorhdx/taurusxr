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

@permit.suproute('/admin/agency/update', u'代理商修改', MenuAgency, order=1.0002)

class UpdateHandler(BaseHandler):

    def mdl2dict(self, *mdls):
        if not mdls:
            return
        data = {}
        for mdl in mdls:
            if not hasattr(mdl, '__table__'):
                return
            for c in mdl.__table__.columns:
                data[c.name] = getattr(mdl, c.name)

        return data

    @authenticated
    def get(self):
        agency_id = self.get_argument('agency_id')
        agency = self.db.query(models.TrAgency).get(agency_id)
        opr = self.db.query(models.TrOperator).filter_by(operator_name=agency.operator_name).first()
        nodes = [ (n.id, n.node_name) for n in self.db.query(models.TrNode) ]
        products = [ (p.id, p.product_name) for p in self.db.query(models.TrProduct) ]
        form = agency_form.agency_update_form(nodes, products)
        form.fill(self.mdl2dict(agency, opr))
        form.operator_pass.set_value('')
        form.agency_id.set_value(agency_id)
        onodes = self.db.query(models.TrOperatorNodes).filter_by(operator_name=form.d.operator_name)
        oproducts = self.db.query(models.TrOperatorProducts).filter_by(operator_name=form.d.operator_name)
        form.operator_products.set_value([ p.product_id for p in oproducts ])
        form.operator_nodes.set_value([ ond.node_id for ond in onodes ])
        rules = self.db.query(models.TrOperatorRule.rule_path).filter_by(operator_name=opr.operator_name)
        rules = [ r[0] for r in rules ]
        return self.render('agency_form.html', form=form, rules=rules)

    @authenticated
    def post(self):
        nodes = [ (n.id, n.node_desc) for n in self.db.query(models.TrNode) ]
        products = [ (p.id, p.product_name) for p in self.db.query(models.TrProduct) ]
        form = agency_form.agency_update_form(nodes, products)
        rules = self.db.query(models.TrOperatorRule.rule_path).filter_by(operator_name=form.d.operator_name)
        rules = [ r[0] for r in rules ]
        if not form.validates(source=self.get_params()):
            return self.render('agency_form.html', form=form, rules=rules)
        manager = AgencyService(self.db, self.aes, operator=self.current_user)
        agency = manager.update(form.d, **dict(operator_nodes=self.get_arguments('operator_nodes'), operator_products=self.get_arguments('operator_products'), rule_item=self.get_arguments('rule_item')))
        if not agency:
            return self.render('agency_form.html', form=form, msg=manager.last_error)
        self.redirect('/admin/agency', permanent=False)