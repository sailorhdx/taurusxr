#!/usr/bin/env python
# coding=utf-8
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.resource import bas_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.toughlib import redis_cache
from toughradius.modules.settings import *
from toughradius.modules.dbservice.bas_service import BasService
from toughradius.modules.events import settings as evset

@permit.route('/admin/bas', u'接入设备管理', MenuRes, order=2.0, is_menu=True)

class BasListHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('bas_list.html', bastype=bas_forms.bastype, bas_list=self.db.query(models.TrBas))


@permit.suproute('/admin/bas/add', u'新增接入设备', MenuRes, order=2.0001)

class BasAddHandler(BaseHandler):

    @authenticated
    def get(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        form = bas_forms.bas_add_form(nodes)
        form.portal_vendor.set_value('0')
        form.coa_port.set_value(3799)
        form.ac_port.set_value(2000)
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        form = bas_forms.bas_add_form(nodes)
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        manager = BasService(self.db, self.aes, operator=self.current_user)
        ret = manager.add(form.d, nodes=self.get_arguments('nodes'))
        if not ret:
            return self.render('base_form.html', form=form, msg=manager.last_error)
        self.redirect('/admin/bas', permanent=False)


@permit.suproute('/admin/bas/update', u'修改接入设备', MenuRes, order=2.0002)

class BasUpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        bas_id = self.get_argument('bas_id')
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        basnodes = [ bn.node_id for bn in self.db.query(models.TrBasNode).filter_by(bas_id=bas_id) ]
        form = bas_forms.bas_update_form(nodes)
        form.fill(self.db.query(models.TrBas).get(bas_id))
        form.nodes.set_value(basnodes)
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        form = bas_forms.bas_update_form(nodes)
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        manager = BasService(self.db, self.aes, operator=self.current_user)
        ret = manager.update(form.d, nodes=self.get_arguments('nodes'))
        if not ret:
            return self.render('base_form.html', form=form, msg=manager.last_error)
        self.redirect('/admin/bas', permanent=False)


@permit.suproute('/admin/bas/delete', u'删除接入设备', MenuRes, order=2.0003)

class BasDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        bas_id = self.get_argument('bas_id')
        manager = BasService(self.db, self.aes, operator=self.current_user)
        ret = manager.delete(bas_id)
        if not ret:
            return self.render_error(msg=manager.last_error)
        self.redirect('/admin/bas', permanent=False)


@permit.suproute('/admin/bas/detail', u'接入设备详情', MenuRes, order=2.0004)

class BasDeleteListHandler(BaseHandler):

    @authenticated
    def get(self):
        bas_id = self.get_argument('bas_id')
        bas = self.db.query(models.TrBas).get(bas_id)
        if not bas:
            return self.render_error(msg=u'接入设备不存在')
        synclogs = self.logtrace.list_trace('routeros') or []
        bas_attrs = self.db.query(models.TrBasAttr).filter_by(bas_id=bas_id)
        return self.render('bas_detail.html', bastype=bas_forms.bastype, synclogs=synclogs, bas=bas, bas_attrs=bas_attrs)
