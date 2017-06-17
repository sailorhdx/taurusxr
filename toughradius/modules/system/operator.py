#!/usr/bin/env python
# coding=utf-8
from hashlib import md5
import cyclone.auth
import cyclone.escape
import cyclone.web
from toughradius.toughlib import utils, dispatch
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.system import operator_form
from toughradius.modules.system.operator_form import opr_status_dict
from toughradius.modules.settings import *
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.common import tools

@permit.suproute('/admin/operator', u'操作员管理', MenuSys, order=3.0, is_menu=True)

class OperatorHandler(BaseHandler):

    @authenticated
    def get(self):
        agency_q = self.db.query(models.TrAgency.operator_name)
        operator_list = self.db.query(models.TrOperator).filter(models.TrOperator.operator_name.notin_(agency_q))
        self.render('operator_list.html', operator_list=operator_list, opr_status=opr_status_dict)


@permit.suproute('/admin/operator/add', u'操作员新增', MenuSys, order=3.0001)

class AddHandler(BaseHandler):

    @authenticated
    def get(self):
        nodes = [ (n.id, n.node_desc) for n in self.db.query(models.TrNode) ]
        products = [ (p.id, p.product_name) for p in self.db.query(models.TrProduct) ]
        self.render('opr_form.html', form=operator_form.operator_add_form(nodes, products), rules=[])

    @authenticated
    def post(self):
        nodes = [ (n.id, n.node_desc) for n in self.db.query(models.TrNode) ]
        products = [ (p.id, p.product_name) for p in self.db.query(models.TrProduct) ]
        form = operator_form.operator_add_form(nodes, products)
        if not form.validates(source=self.get_params()):
            return self.render('opr_form.html', form=form, rules=self.get_arguments('rule_item'))
        if self.db.query(models.TrOperator.id).filter_by(operator_name=form.d.operator_name).count() > 0:
            return self.render('opr_form.html', form=form, msg=u'操作员已经存在', rules=self.get_arguments('rule_item'))
        operator = models.TrOperator()
        operator.id = utils.get_uuid()
        operator.operator_name = form.d.operator_name
        operator.operator_pass = md5(form.d.operator_pass.encode()).hexdigest()
        operator.operator_type = 1
        operator.operator_desc = form.d.operator_desc
        operator.operator_status = form.d.operator_status
        operator.sync_ver = tools.gen_sync_ver()
        self.db.add(operator)
        self.add_oplog(u'新增操作员信息:%s' % utils.safeunicode(operator.operator_name))
        for node_id in self.get_arguments('operator_nodes'):
            onode = models.TrOperatorNodes()
            onode.operator_name = form.d.operator_name
            onode.node_id = node_id
            onode.sync_ver = tools.gen_sync_ver()
            self.db.add(onode)

        for product_id in self.get_arguments('operator_products'):
            oproduct = models.TrOperatorProducts()
            oproduct.operator_name = form.d.operator_name
            oproduct.product_id = product_id
            oproduct.sync_ver = tools.gen_sync_ver()
            self.db.add(oproduct)

        for path in self.get_arguments('rule_item'):
            item = permit.get_route(path)
            if not item:
                continue
            rule = models.TrOperatorRule()
            rule.id = utils.get_uuid()
            rule.operator_name = operator.operator_name
            rule.rule_name = item['name']
            rule.rule_path = item['path']
            rule.rule_category = item['category']
            rule.sync_ver = tools.gen_sync_ver()
            self.db.add(rule)

        self.db.commit()
        for rule in self.db.query(models.TrOperatorRule).filter_by(operator_name=operator.operator_name):
            permit.bind_opr(rule.operator_name, rule.rule_path)

        self.redirect('/admin/operator', permanent=False)


@permit.suproute('/admin/operator/update', u'操作员修改', MenuSys, order=3.0002)

class UpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        operator_id = self.get_argument('operator_id')
        opr = self.db.query(models.TrOperator).get(operator_id)
        nodes = [ (n.id, n.node_name) for n in self.db.query(models.TrNode) ]
        products = [ (p.id, p.product_name) for p in self.db.query(models.TrProduct) ]
        form = operator_form.operator_update_form(nodes, products)
        form.fill(self.db.query(models.TrOperator).get(operator_id))
        form.operator_pass.set_value('')
        onodes = self.db.query(models.TrOperatorNodes).filter_by(operator_name=form.d.operator_name)
        oproducts = self.db.query(models.TrOperatorProducts).filter_by(operator_name=form.d.operator_name)
        form.operator_products.set_value([ p.product_id for p in oproducts ])
        form.operator_nodes.set_value([ ond.node_id for ond in onodes ])
        rules = self.db.query(models.TrOperatorRule.rule_path).filter_by(operator_name=opr.operator_name)
        rules = [ r[0] for r in rules ]
        return self.render('opr_form.html', form=form, rules=rules)

    @authenticated
    def post(self):
        nodes = [ (n.id, n.node_desc) for n in self.db.query(models.TrNode) ]
        products = [ (p.id, p.product_name) for p in self.db.query(models.TrProduct) ]
        form = operator_form.operator_update_form(nodes, products)
        if not form.validates(source=self.get_params()):
            rules = self.db.query(models.TrOperatorRule.rule_path).filter_by(operator_name=form.d.operator_name)
            rules = [ r[0] for r in rules ]
            return self.render('opr_form.html', form=form, rules=rules)
        operator = self.db.query(models.TrOperator).get(form.d.id)
        if form.d.operator_pass:
            operator.operator_pass = md5(form.d.operator_pass.encode()).hexdigest()
        operator.operator_desc = form.d.operator_desc
        operator.operator_status = form.d.operator_status
        operator.sync_ver = tools.gen_sync_ver()
        self.db.query(models.TrOperatorNodes).filter_by(operator_name=operator.operator_name).delete()
        for node_id in self.get_arguments('operator_nodes'):
            onode = models.TrOperatorNodes()
            onode.operator_name = form.d.operator_name
            onode.node_id = node_id
            onode.sync_ver = tools.gen_sync_ver()
            self.db.add(onode)

        self.db.query(models.TrOperatorProducts).filter_by(operator_name=operator.operator_name).delete()
        for product_id in self.get_arguments('operator_products'):
            oproduct = models.TrOperatorProducts()
            oproduct.operator_name = form.d.operator_name
            oproduct.product_id = product_id
            oproduct.sync_ver = tools.gen_sync_ver()
            self.db.add(oproduct)

        self.add_oplog(u'修改操作员%s信息' % utils.safeunicode(operator.operator_name))
        self.db.query(models.TrOperatorRule).filter_by(operator_name=operator.operator_name).delete()
        for path in self.get_arguments('rule_item'):
            item = permit.get_route(path)
            if not item:
                continue
            rule = models.TrOperatorRule()
            rule.id = utils.get_uuid()
            rule.operator_name = operator.operator_name
            rule.rule_name = item['name']
            rule.rule_path = item['path']
            rule.rule_category = item['category']
            rule.sync_ver = tools.gen_sync_ver()
            self.db.add(rule)

        permit.unbind_opr(operator.operator_name)
        self.db.commit()
        for rule in self.db.query(models.TrOperatorRule).filter_by(operator_name=operator.operator_name):
            permit.bind_opr(rule.operator_name, rule.rule_path)

        self.redirect('/admin/operator', permanent=False)


@permit.suproute('/admin/operator/delete', u'操作员删除', MenuSys, order=3.0003)

class DeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        operator_id = self.get_argument('operator_id')
        opr = self.db.query(models.TrOperator).get(operator_id)
        self.db.query(models.TrOperatorRule).filter_by(operator_name=opr.operator_name).delete()
        self.db.query(models.TrOperator).filter_by(id=operator_id).delete()
        self.add_oplog(u'删除操作员%s信息' % utils.safeunicode(opr.operator_name))
        self.db.commit()
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOperatorRule.__tablename__, dict(id=operator_id)), async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOperator.__tablename__, dict(id=operator_id)), async=True)
        self.redirect('/admin/operator', permanent=False)