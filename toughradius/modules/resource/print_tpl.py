#!/usr/bin/env python
# coding=utf-8
import os
import cyclone.auth
import cyclone.escape
import cyclone.web
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.resource import print_tpl_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.modules.settings import *
from toughradius.common import tools
if os.environ.get('LICENSE_TYPE') != 'community':

    @permit.route('/admin/printtpl', u'票据模板管理', MenuRes, order=5.0, is_menu=True)

    class ContentTplListHandler(BaseHandler):

        @authenticated
        def get(self):
            tpls = self.db.query(models.TrPrintTemplate)
            return self.render('print_tpl_list.html', tpls=tpls)


    @permit.suproute('/admin/printtpl/add', u'新增票据模板', MenuRes, order=5.0001)

    class ContentTplAddHandler(BaseHandler):

        @authenticated
        def get(self):
            form = print_tpl_forms.print_tpl_add_form()
            self.render('base_form.html', form=form)

        @authenticated
        def post(self):
            form = print_tpl_forms.print_tpl_add_form()
            if not form.validates(source=self.get_params()):
                return self.render('base_form.html', form=form)
            if self.db.query(models.TrPrintTemplate).filter_by(tpl_name=form.d.tpl_name).count() > 0:
                return self.render('base_form.html', form=form, msg=u'模板名已经存在')
            tpl = models.TrPrintTemplate()
            tpl.id = utils.get_uuid()
            tpl.tpl_name = form.d.tpl_name
            tpl.tpl_content = utils.safeunicode(form.d.tpl_content)
            tpl.sync_ver = tools.gen_sync_ver()
            self.db.add(tpl)
            for tpl_type in self.get_arguments('tpl_types'):
                tpltype = models.TrPrintTemplateTypes()
                tpltype.tpl_id = tpl.id
                tpltype.tpl_type = tpl_type
                tpltype.sync_ver = tools.gen_sync_ver()
                self.db.add(tpltype)

            self.add_oplog(u'新增票据模板信息:%s' % utils.safeunicode(form.d.tpl_name))
            self.db.commit()
            self.redirect('/admin/printtpl', permanent=False)


    @permit.suproute('/admin/printtpl/update', u'修改票据模板', MenuRes, order=5.0002)

    class ContentTplUpdateHandler(BaseHandler):

        @authenticated
        def get(self):
            tpl_id = self.get_argument('tpl_id')
            tpltypes = self.db.query(models.TrPrintTemplateTypes).filter_by(tpl_id=tpl_id)
            form = print_tpl_forms.print_tpl_update_form()
            tpl = self.db.query(models.TrPrintTemplate).get(tpl_id)
            form.fill(tpl)
            form.tpl_types.set_value([ n.tpl_type for n in tpltypes ])
            self.render('base_form.html', form=form)

        @authenticated
        def post(self):
            form = print_tpl_forms.print_tpl_update_form()
            if not form.validates(source=self.get_params()):
                return self.render('base_form.html', form=form)
            tpl = self.db.query(models.TrPrintTemplate).get(form.d.id)
            tpl.tpl_name = form.d.tpl_name
            tpl.tpl_content = utils.safeunicode(form.d.tpl_content)
            tpl.sync_ver = tools.gen_sync_ver()
            self.db.query(models.TrPrintTemplateTypes).filter_by(tpl_id=tpl.id).delete()
            for tpl_type in self.get_arguments('tpl_types'):
                tpltype = models.TrPrintTemplateTypes()
                tpltype.tpl_id = tpl.id
                tpltype.tpl_type = tpl_type
                tpltype.sync_ver = tools.gen_sync_ver()
                self.db.add(tpltype)

            self.add_oplog(u'修改票据模板信息:%s' % utils.safeunicode(form.d.tpl_name))
            self.db.commit()
            self.redirect('/admin/printtpl', permanent=False)


    @permit.suproute('/admin/printtpl/design', u'设计票据模板', MenuRes, order=5.0003)

    class PrintDesignHandler(BaseHandler):

        def post(self):
            tpl_id = self.get_argument('tpl_id')
            tpl = self.db.query(models.TrPrintTemplate).get(tpl_id)
            self.render_json(func=tpl.tpl_content)


    @permit.suproute('/admin/printtpl/delete', u'删除票据模板', MenuRes, order=5.0004)

    class ContentTplDeleteHandler(BaseHandler):

        @authenticated
        def get(self):
            tpl_id = self.get_argument('tpl_id')
            self.db.query(models.TrPrintTemplate).filter_by(id=tpl_id).delete()
            self.add_oplog(u'删除票据模板信息:%s' % tpl_id)
            self.db.commit()
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrPrintTemplate.__tablename__, dict(id=tpl_id)), async=True)
            self.redirect('/admin/printtpl', permanent=False)