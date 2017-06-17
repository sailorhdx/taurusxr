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
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.modules.dbservice.agency_service import AgencyService
from toughradius.toughlib.utils import safeunicode as _su

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