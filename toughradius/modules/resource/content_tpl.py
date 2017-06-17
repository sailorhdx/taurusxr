#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.resource import content_tpl_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.modules.settings import *
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.common import tools

@permit.route('/admin/contenttpl', u'通知模板管理', MenuRes, order=4.0, is_menu=True)

class ContentTplListHandler(BaseHandler):

    @authenticated
    def get(self):
        tpls = self.db.query(models.TrContentTemplate)
        return self.render('content_tpl_list.html', tpls=tpls, tpl_types=content_tpl_forms.tpl_types)


@permit.suproute('/admin/contenttpl/add', u'新增内容模板', MenuRes, order=4.0001)

class ContentTplAddHandler(BaseHandler):

    @authenticated
    def get(self):
        form = content_tpl_forms.content_tpl_add_form()
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = content_tpl_forms.content_tpl_add_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        if self.db.query(models.TrContentTemplate).filter_by(tpl_type=form.d.tpl_type).count() > 0:
            return self.render('base_form.html', form=form, msg=u'模板已经存在')
        tpl = models.TrContentTemplate()
        tpl.id = utils.get_uuid()
        tpl.tpl_type = form.d.tpl_type
        tpl.tpl_id = form.d.tpl_id
        tpl.tpl_content = form.d.tpl_content
        tpl.sync_ver = tools.gen_sync_ver()
        self.db.add(tpl)
        self.add_oplog(u'新增模板信息:%s' % form.d.tpl_type)
        self.db.commit()
        self.redirect('/admin/contenttpl', permanent=False)


@permit.suproute('/admin/contenttpl/update', u'修改内容模板', MenuRes, order=4.0002)

class ContentTplUpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        tpl_id = self.get_argument('tpl_id')
        form = content_tpl_forms.content_tpl_update_form()
        tpl = self.db.query(models.TrContentTemplate).get(tpl_id)
        form.fill(tpl)
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = content_tpl_forms.content_tpl_update_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        tpl = self.db.query(models.TrContentTemplate).get(form.d.id)
        tpl.tpl_type = form.d.tpl_type
        tpl.tpl_id = form.d.tpl_id
        tpl.tpl_content = form.d.tpl_content
        tpl.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'修改模板信息:%s' % form.d.tpl_type)
        self.db.commit()
        self.redirect('/admin/contenttpl', permanent=False)


@permit.suproute('/admin/contenttpl/delete', u'删除内容模板', MenuRes, order=4.0003)

class ContentTplDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        tpl_id = self.get_argument('tpl_id')
        self.db.query(models.TrContentTemplate).filter_by(id=tpl_id).delete()
        self.add_oplog(u'删除模板信息:%s' % tpl_id)
        self.db.commit()
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrContentTemplate.__tablename__, dict(id=tpl_id)), async=True)
        self.redirect('/admin/contenttpl', permanent=False)