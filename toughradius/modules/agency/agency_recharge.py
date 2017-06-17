#!/usr/bin/env python
# coding=utf-8
from hashlib import md5
from toughradius.toughlib import utils
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.agency import agency_form
from toughradius.modules.agency.agency_form import opr_status_dict
from toughradius.modules.settings import *
from toughradius.modules.dbservice.agency_service import AgencyService

@permit.suproute('/admin/agency/recharge', u'代理商充值', MenuAgency, order=1.0002)

class AgencyRechangeHandler(BaseHandler):

    @authenticated
    def get(self):
        agency_id = self.get_argument('agency_id')
        agency = self.db.query(models.TrAgency).get(agency_id)
        form = agency_form.agency_recharge_form()
        form.agency_id.set_value(agency_id)
        form.agency_name.set_value(agency.agency_name)
        return self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = agency_form.agency_recharge_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        manager = AgencyService(self.db, self.aes, operator=self.current_user)
        agency = manager.recharge(form.d)
        if not agency:
            return self.render('base_form.html', form=form, msg=manager.last_error)
        self.redirect('/admin/agency', permanent=False)