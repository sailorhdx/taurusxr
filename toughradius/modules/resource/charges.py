#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.resource import charges_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.modules.settings import *
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.common import tools

@permit.route('/admin/charge', u'收费项目管理', MenuRes, order=7.0, is_menu=True)

class ChargeListHandler(BaseHandler):

    @authenticated
    def get(self):
        charges = self.db.query(models.TrCharges)
        return self.render('charge_list.html', charges=charges)


@permit.suproute('/admin/charge/add', u'新增收费项目', MenuRes, order=7.0001)

class ChargeAddHandler(BaseHandler):

    @authenticated
    def get(self):
        form = charges_forms.charge_add_form()
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = charges_forms.charge_add_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        if self.db.query(models.TrCharges).filter_by(charge_code=form.d.charge_code).count() > 0:
            return self.render('base_form.html', form=form, msg=u'收费项已经存在')
        charge = models.TrCharges()
        charge.charge_code = form.d.charge_code
        charge.charge_name = form.d.charge_name
        charge.charge_value = utils.yuan2fen(form.d.charge_value)
        charge.charge_desc = form.d.charge_desc
        charge.sync_ver = tools.gen_sync_ver()
        self.db.add(charge)
        self.add_oplog(u'新增收费项信息:%s' % utils.safeunicode(form.d.charge_name))
        self.db.commit()
        self.redirect('/admin/charge', permanent=False)


@permit.suproute('/admin/charge/update', u'修改收费项目', MenuRes, order=7.0002)

class ChargeUpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        charge_code = self.get_argument('charge_code')
        form = charges_forms.charge_update_form()
        charge = self.db.query(models.TrCharges).get(charge_code)
        form.fill(charge)
        form.charge_value.set_value(utils.fen2yuan(charge.charge_value))
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = charges_forms.charge_update_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        charge = self.db.query(models.TrCharges).get(form.d.charge_code)
        charge.charge_name = form.d.charge_name
        charge.charge_value = utils.yuan2fen(form.d.charge_value)
        charge.charge_desc = form.d.charge_desc
        charge.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'修改收费项信息:%s' % utils.safeunicode(form.d.charge_name))
        self.db.commit()
        self.redirect('/admin/charge', permanent=False)


@permit.suproute('/admin/charge/delete', u'删除收费项目', MenuRes, order=7.0004)

class ChargeDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        charge_code = self.get_argument('charge_code')
        self.db.query(models.TrCharges).filter_by(charge_code=charge_code).delete()
        self.add_oplog(u'删除收费项信息:%s' % charge_code)
        self.db.commit()
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrCharges.__tablename__, dict(charge_code=charge_code)), async=True)
        self.redirect('/admin/charge', permanent=False)