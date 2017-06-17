#!/usr/bin/env python
# coding=utf-8
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.region import node_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules.settings import *
from toughradius.modules.dbservice.node_service import NodeService

@permit.route('/admin/node', u'区域节点管理', MenuNode, order=1.0, is_menu=True)

class NodeListHandler(BaseHandler):

    @authenticated
    def get(self):
        nodes = self.db.query(models.TrNode)
        return self.render('node_list.html', nodes=nodes)


@permit.suproute('/admin/node/add', u'新增区域', MenuNode, order=1.0001)

class NodeAddHandler(BaseHandler):

    @authenticated
    def get(self):
        arules = [ (r.id, r.rule_name) for r in self.db.query(models.TrAccountRule) ]
        basids = [ (r.id, r.bas_name) for r in self.db.query(models.TrBas) ]
        form = node_forms.node_add_form(rule_ids=arules, bas_ids=basids)
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        arules = [ (r.id, r.rule_name) for r in self.db.query(models.TrAccountRule) ]
        basids = [ (r.id, r.bas_name) for r in self.db.query(models.TrBas) ]
        form = node_forms.node_add_form(rule_ids=arules, bas_ids=basids)
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        manager = NodeService(self.db, self.aes, operator=self.current_user)
        ret = manager.add(form.d, bas_ids=self.get_arguments('bas_id'))
        if not ret:
            return self.render('base_form.html', form=form, msg=manager.last_error)
        self.redirect('/admin/node', permanent=False)


@permit.suproute('/admin/node/update', u'修改区域', MenuNode, order=1.0002)

class NodeUpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        arules = [ (r.id, r.rule_name) for r in self.db.query(models.TrAccountRule) ]
        basids = [ (r.id, r.bas_name) for r in self.db.query(models.TrBas) ]
        node_id = self.get_argument('node_id')
        basnodes = [ bn.bas_id for bn in self.db.query(models.TrBasNode).filter_by(node_id=node_id) ]
        form = node_forms.node_update_form(rule_ids=arules, bas_ids=basids)
        node = self.db.query(models.TrNode).get(node_id)
        form.fill(node)
        form.bas_id.set_value(basnodes)
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        arules = [ (r.id, r.rule_name) for r in self.db.query(models.TrAccountRule) ]
        basids = [ (r.id, r.bas_name) for r in self.db.query(models.TrBas) ]
        form = node_forms.node_update_form(rule_ids=arules, bas_ids=basids)
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        manager = NodeService(self.db, self.aes, operator=self.current_user)
        ret = manager.update(form.d, bas_ids=self.get_arguments('bas_id'))
        if not ret:
            return self.render('base_form.html', form=form, msg=manager.last_error)
        self.redirect('/admin/node', permanent=False)


@permit.suproute('/admin/node/delete', u'删除区域', MenuNode, order=1.0003)

class NodeDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        node_id = self.get_argument('node_id')
        manager = NodeService(self.db, self.aes, operator=self.current_user)
        ret = manager.delete(node_id)
        if not ret:
            return self.render_error(msg=manager.last_error)
        self.redirect('/admin/node', permanent=False)