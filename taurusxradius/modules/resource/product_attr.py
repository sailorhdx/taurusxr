#!/usr/bin/env python
# coding=utf-8
from taurusxradius.modules import models
from taurusxradius.modules.base import BaseHandler, authenticated
from taurusxradius.modules.resource import product_forms
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, dispatch
from taurusxradius.modules.radius.radius_attrs import radius_attrs
from taurusxradius.modules.events.settings import DBSYNC_STATUS_ADD
from taurusxradius.modules.settings import *
from taurusxradius.common import tools

@permit.suproute('/admin/product/attr/add', u'新增资费属性', MenuRes, order=3.0001)

class ProductAddListHandler(BaseHandler):

    @authenticated
    def get(self):
        product_id = self.get_argument('product_id')
        if self.db.query(models.TrProduct).filter_by(id=product_id).count() <= 0:
            return self.render_error(msg=u'资费不存在')
        form = product_forms.product_attr_add_form()
        form.product_id.set_value(product_id)
        return self.render('pattr_form.html', form=form, pattrs=radius_attrs)

    def post(self):
        form = product_forms.product_attr_add_form()
        if not form.validates(source=self.get_params()):
            return self.render('pattr_form.html', form=form, pattrs=radius_attrs)
        attr = models.TrProductAttr()
        attr.id = utils.get_uuid()
        attr.product_id = form.d.product_id
        attr.attr_type = form.d.attr_type
        attr.attr_name = form.d.attr_name
        attr.attr_value = form.d.attr_value
        attr.attr_desc = form.d.attr_desc
        attr.sync_ver = tools.gen_sync_ver()
        self.db.add(attr)
        self.add_oplog(u'新增资费属性信息:%s' % attr.attr_name)
        self.db.commit()
        self.redirect('/admin/product/detail?product_id=%s' % form.d.product_id)


@permit.suproute('/admin/product/attr/update', u'修改资费属性', MenuRes, order=3.0002)

class ProductUpdateListHandler(BaseHandler):

    @authenticated
    def get(self):
        attr_id = self.get_argument('attr_id')
        attr = self.db.query(models.TrProductAttr).get(attr_id)
        form = product_forms.product_attr_update_form()
        form.fill(attr)
        return self.render('pattr_form.html', form=form, pattrs=radius_attrs)

    def post(self):
        form = product_forms.product_attr_update_form()
        if not form.validates(source=self.get_params()):
            return self.render('pattr_form.html', form=form, pattrs=radius_attrs)
        attr = self.db.query(models.TrProductAttr).get(form.d.id)
        attr.attr_type = form.d.attr_type
        attr.attr_name = form.d.attr_name
        attr.attr_value = form.d.attr_value
        attr.attr_desc = form.d.attr_desc
        attr.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'修改资费属性信息:%s' % attr.attr_name)
        self.db.commit()
        self.redirect('/admin/product/detail?product_id=%s' % form.d.product_id)


@permit.suproute('/admin/product/attr/delete', u'删除资费属性', MenuRes, order=3.0003)

class ProductDeleteListHandler(BaseHandler):

    @authenticated
    def get(self):
        attr_id = self.get_argument('attr_id')
        attr = self.db.query(models.TrProductAttr).get(attr_id)
        product_id = attr.product_id
        self.db.query(models.TrProductAttr).filter_by(id=attr_id).delete()
        self.add_oplog(u'删除资费属性信息:%s' % attr.attr_name)
        self.db.commit()
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrProductAttr.__tablename__, dict(id=attr_id)), async=True)
        self.redirect('/admin/product/detail?product_id=%s' % product_id)