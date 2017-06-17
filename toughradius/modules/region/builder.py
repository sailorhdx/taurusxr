#!/usr/bin/env python
# coding=utf-8
import os
import cyclone.auth
import cyclone.escape
import cyclone.web
import datetime
import random
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.region import builder_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch, logger
from toughradius.modules.settings import *
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.common import tools

@permit.route('/admin/builder', u'服务人员管理', MenuNode, order=8.0, is_menu=True)

class BuilderHandler(BaseHandler):

    @authenticated
    def get(self):
        areas = [ (a.id, n + ' -> ' + a.area_name) for n, a in self.get_opr_areas() ]
        builders = self.db.query(models.TrBuilder)
        return self.render('builder_list.html', builders=builders, areas=areas)


@permit.suproute('/admin/builder/add', u'新增服务人员', MenuNode, order=8.0001)

class BuilderAddHandler(BaseHandler):

    @authenticated
    def get(self):
        areas = [ (a.id, n + ' -> ' + a.area_name) for n, a in self.get_opr_areas() ]
        form = builder_forms.builder_add_form(areas)
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        areas = [ (a.id, n + ' -> ' + a.area_name) for n, a in self.get_opr_areas() ]
        form = builder_forms.builder_add_form(areas)
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        builder = models.TrBuilder()
        builder.id = utils.get_uuid()
        builder.builder_name = form.d.builder_name
        builder.builder_phone = form.d.builder_phone
        builder.mp_active_code = random.randint(100000, 999999)
        builder.sync_ver = tools.gen_sync_ver()
        self.db.add(builder)
        for area_id in self.get_arguments('areas'):
            area_builder = models.TrAreaBuilder()
            area_builder.area_id = area_id
            area_builder.builder_id = builder.id
            self.db.add(area_builder)

        self.add_oplog(u'新增服务人员:%s' % utils.safeunicode(form.d.builder_name))
        self.db.commit()
        self.redirect('/admin/builder', permanent=False)


@permit.suproute('/admin/builder/update', u'修改服务人员', MenuNode, order=8.0002)

class BuilderUpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        builder_id = self.get_argument('builder_id')
        areas = [ (a.id, n + ' -> ' + a.area_name) for n, a in self.get_opr_areas() ]
        form = builder_forms.builder_update_form(areas)
        abuilders = self.db.query(models.TrAreaBuilder).filter_by(builder_id=builder_id)
        builder = self.db.query(models.TrBuilder).get(builder_id)
        form.fill(builder)
        form.areas.set_value([ ab.area_id for ab in abuilders ])
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        areas = [ (a.id, n + ' -> ' + a.area_name) for n, a in self.get_opr_areas() ]
        form = builder_forms.builder_update_form(areas)
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        builder = self.db.query(models.TrBuilder).get(form.d.id)
        builder.builder_name = form.d.builder_name
        builder.builder_phone = form.d.builder_phone
        builder.sync_ver = tools.gen_sync_ver()
        self.db.query(models.TrAreaBuilder).filter_by(builder_id=builder.id).delete()
        for area_id in self.get_arguments('areas'):
            area_builder = models.TrAreaBuilder()
            area_builder.area_id = area_id
            area_builder.builder_id = builder.id
            area_builder.sync_ver = tools.gen_sync_ver()
            self.db.add(area_builder)

        self.add_oplog(u'修改服务人员:%s' % utils.safeunicode(form.d.builder_name))
        self.db.commit()
        self.redirect('/admin/builder', permanent=False)


@permit.suproute('/admin/builder/delete', u'删除服务人员', MenuNode, order=8.0003)

class BuilderDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        builder_id = self.get_argument('builder_id')
        self.db.query(models.TrBuilder).filter_by(id=builder_id).delete()
        self.db.query(models.TrAreaBuilder).filter_by(builder_id=builder_id).delete()
        self.add_oplog(u'删除服务人员:%s' % builder_id)
        self.db.commit()
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrBuilder.__tablename__, dict(id=builder_id)), async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAreaBuilder.__tablename__, dict(builder_id=builder_id)), async=True)
        self.redirect('/admin/builder', permanent=False)


if os.environ.get('LICENSE_TYPE') != 'community':

    @permit.route('/admin/builder/qrcode/new', u'服务人员二维码创建', MenuNode, order=8.0005, is_menu=False)

    class BuilderQrcodeAddHandler(BaseHandler):

        @authenticated
        def post(self, template_variables = {}):
            builder_id = self.get_argument('builder_id')
            builder = self.db.query(models.TrBuilder).get(builder_id)
            if not builder:
                self.render_json(code=1, msg=u'服务人员不存在')
                return
            if builder.wechat_oid:
                self.render_json(code=1, msg=u'服务人员已绑定')
            scene_str = 'oprbind_qr_%s' % builder_id
            req = dict(action_name='QR_LIMIT_STR_SCENE', action_info={'scene': {'scene_str': scene_str}})
            try:
                resp = self.wechat.create_qrcode(req)
            except Exception as err:
                logger.exception(err)
                self.render_json(code=1, msg=u'创建二维码失败')
                return

            qrcode_url = 'https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=%s' % resp.get('ticket')
            builder.mp_qrcode = qrcode_url
            self.db.commit()
            self.render_json(code=0, msg='ok')


    @permit.route('/admin/builder/unbind', u'服务人员微信解绑', MenuNode, order=8.0006, is_menu=False)

    class BuilderUnbindHandler(BaseHandler):

        @authenticated
        def post(self, template_variables = {}):
            builder_id = self.get_argument('builder_id')
            builder = self.db.query(models.TrBuilder).get(builder_id)
            if not builder:
                self.render_json(code=1, msg=u'服务人员不存在')
                return
            else:
                builder.wechat_oid = None
                self.db.commit()
                self.render_json(code=0, msg=u'操作成功')
                return