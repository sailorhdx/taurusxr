#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.region import area_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.modules.settings import *
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.common import tools

@permit.route('/admin/area', u'社区节点管理', MenuNode, order=1.00001, is_menu=True)

class NodeListHandler(BaseHandler):

    @authenticated
    def get(self):
        opr_nodes = self.get_opr_nodes()
        first_nid = opr_nodes[0].id if opr_nodes else ''
        node_id = self.get_argument('node_id', first_nid)
        areas = self.db.query(models.TrArea).filter_by(node_id=node_id)
        return self.render('area_list.html', node_list=opr_nodes, page_data=self.get_page_data(areas), node_id=node_id)

    @authenticated
    def post(self):
        opr_nodes = self.get_opr_nodes()
        node_id = self.get_argument('node_id', '')
        areas = self.db.query(models.TrArea)
        if node_id:
            areas = areas.filter_by(node_id=node_id)
        return self.render('area_list.html', node_list=opr_nodes, page_data=self.get_page_data(areas), **self.get_params())


@permit.suproute('/admin/area/add', u'新增社区', MenuNode, order=1.00011)

class NodeAddHandler(BaseHandler):

    @authenticated
    def get(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        form = area_forms.area_add_form(nodes=nodes)
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        form = area_forms.area_add_form(nodes=nodes)
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        area = models.TrArea()
        area.id = utils.get_uuid()
        area.area_name = form.d.area_name
        area.node_id = form.d.node_id
        area.area_desc = form.d.area_desc
        area.addr_desc = form.d.addr_desc
        area.sync_ver = tools.gen_sync_ver()
        self.db.add(area)
        self.add_oplog(u'新增社区信息:%s' % utils.safeunicode(form.d.area_name))
        self.db.commit()
        self.redirect('/admin/area?node_id=%s' % area.node_id, permanent=False)


@permit.suproute('/admin/area/update', u'修改社区', MenuNode, order=1.00022)

class NodeUpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        area_id = self.get_argument('area_id')
        form = area_forms.area_update_form(nodes=nodes)
        area = self.db.query(models.TrArea).get(area_id)
        form.fill(area)
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        form = area_forms.area_update_form(nodes=nodes)
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        area = self.db.query(models.TrArea).get(form.d.id)
        area.area_name = form.d.area_name
        area.node_id = form.d.node_id
        area.area_desc = form.d.area_desc
        area.addr_desc = form.d.addr_desc
        area.sync_ver = tools.gen_sync_ver()
        self.db.query(models.TrCustomer).filter(models.TrCustomer.area_id == area.id).update({models.TrCustomer.node_id: area.node_id})
        self.add_oplog(u'修改社区信息:%s' % utils.safeunicode(form.d.area_name))
        self.db.commit()
        self.redirect('/admin/area?node_id=%s' % area.node_id, permanent=False)


@permit.suproute('/admin/area/delete', u'删除社区', MenuNode, order=1.00033)

class NodeDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        area_id = self.get_argument('area_id')
        node_id = self.db.query(models.TrArea.node_id).filter_by(id=area_id).scalar()
        if self.db.query(models.TrCustomer.customer_id).filter_by(area_id=area_id).count() > 0:
            return self.render_error(msg=u'该社区下有用户，不允许删除')
        self.db.query(models.TrArea).filter_by(id=area_id).delete()
        self.db.query(models.TrAreaBuilder).filter_by(area_id=area_id).delete()
        self.add_oplog(u'删除社区信息:%s' % area_id)
        self.db.commit()
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrArea.__tablename__, dict(id=area_id)), async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAreaBuilder.__tablename__, dict(area_id=area_id)), async=True)
        self.redirect('/admin/area?node_id=%s' % node_id, permanent=False)