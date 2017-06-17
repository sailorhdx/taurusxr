#!/usr/bin/env python
# coding=utf-8
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.resource import bas_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.modules.events.settings import ROSSYNC_RELOAD
from toughradius.modules.events.settings import CACHE_DELETE_EVENT
from toughradius.modules.settings import *
from toughradius.common import tools

@permit.suproute('/admin/bas/attr/add', u'新增BAS属性', MenuRes, order=3.0001)

class BasAddListHandler(BaseHandler):

    @authenticated
    def get(self):
        bas_id = self.get_argument('bas_id')
        if self.db.query(models.TrBas).filter_by(id=bas_id).count() <= 0:
            return self.render_error(msg=u'BAS不存在')
        form = bas_forms.bas_attr_add_form()
        form.bas_id.set_value(bas_id)
        return self.render('basattr_form.html', form=form)

    def post(self):
        form = bas_forms.bas_attr_add_form()
        if not form.validates(source=self.get_params()):
            return self.render('basattr_form.html', form=form, pattrs=radius_attrs)
        attr = models.TrBasAttr()
        attr.id = utils.get_uuid()
        attr.bas_id = form.d.bas_id
        attr.attr_name = form.d.attr_name
        attr.attr_value = form.d.attr_value
        attr.attr_desc = form.d.attr_desc
        attr.sync_ver = tools.gen_sync_ver()
        self.db.add(attr)
        self.add_oplog(u'新增BAS属性信息:%s' % attr.attr_name)
        self.db.commit()
        self.redirect('/admin/bas/detail?bas_id=%s' % form.d.bas_id)


@permit.suproute('/admin/bas/attr/update', u'修改BAS属性', MenuRes, order=3.0002)

class BasUpdateListHandler(BaseHandler):

    @authenticated
    def get(self):
        attr_id = self.get_argument('attr_id')
        attr = self.db.query(models.TrBasAttr).get(attr_id)
        form = bas_forms.bas_attr_update_form()
        form.fill(attr)
        if attr.attr_name in ('ros_api_pwd',):
            form.attr_value.set_value('')
        return self.render('basattr_form.html', form=form)

    def post(self):
        form = bas_forms.bas_attr_update_form()
        if not form.validates(source=self.get_params()):
            return self.render('basattr_form.html', form=form)
        attr = self.db.query(models.TrBasAttr).get(form.d.id)
        attr.attr_name = form.d.attr_name
        attr.attr_value = form.d.attr_value
        attr.attr_desc = form.d.attr_desc
        attr.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'修改BAS属性信息:%s' % attr.attr_name)
        self.db.commit()
        dispatch.pub(CACHE_DELETE_EVENT, bas_attr_cache_key(form.d.bas_id, attr.attr_name), async=True)
        dispatch.pub(ROSSYNC_RELOAD, form.d.bas_id, async=True)
        self.redirect('/admin/bas/detail?bas_id=%s' % form.d.bas_id)


@permit.suproute('/admin/bas/attr/delete', u'删除BAS属性', MenuRes, order=3.0003)

class BasDeleteListHandler(BaseHandler):

    @authenticated
    def get(self):
        attr_id = self.get_argument('attr_id')
        attr = self.db.query(models.TrBasAttr).get(attr_id)
        bas_id = attr.bas_id
        self.db.query(models.TrBasAttr).filter_by(id=attr_id).delete()
        self.add_oplog(u'删除BAS属性信息:%s' % attr.attr_name)
        self.db.commit()
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrBasAttr.__tablename__, dict(id=attr_id)), async=True)
        self.redirect('/admin/bas/detail?bas_id=%s' % bas_id)
