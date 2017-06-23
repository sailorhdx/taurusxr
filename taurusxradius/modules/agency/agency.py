#!/usr/bin/env python
# coding=utf-8
from hashlib import md5
from taurusxradius.taurusxlib import utils
from taurusxradius.modules.base import BaseHandler, authenticated
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules import models
from taurusxradius.modules.agency import agency_form
from taurusxradius.modules.agency.agency_form import opr_status_dict
from taurusxradius.modules.settings import *
from taurusxradius.modules.events.settings import DBSYNC_STATUS_ADD
from taurusxradius.modules.dbservice.agency_service import AgencyService
from taurusxradius.taurusxlib.utils import safeunicode as _su

@permit.suproute('/admin/agency', u'代理商管理', MenuAgency, order=1.0, is_menu=True)

class AgencyHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('agency_list.html', agency_list=self.db.query(models.TrAgency))


@permit.suproute('/admin/agency/delete', u'代理商删除', MenuAgency, order=1.0003)

class AgencyDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        agency_id = self.get_argument('agency_id')
        manager = AgencyService(self.db, self.aes, operator=self.current_user)
        if not manager.delete(agency_id):
            return self.render_error(msg=manager.last_error)
        self.redirect('/admin/agency', permanent=False)