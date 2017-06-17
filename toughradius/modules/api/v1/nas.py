#!/usr/bin/env python
# coding=utf-8
import time
import traceback
from toughradius.toughlib import utils, apiutils, dispatch, logger
from toughradius.toughlib.permit import permit
from toughradius.modules.api.apibase import ApiHandler
from toughradius.modules.api.apibase import authapi
from toughradius.modules import models
from toughradius.modules.dbservice.bas_service import BasService

@permit.route('/api/v1/nas/query')

class NasQueryHandler(ApiHandler):

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            ip_addr = formdata.get('ip_addr')
            nass = self.db.query(models.TrBas)
            if ip_addr:
                nass = nass.filter_by(ip_addr=ip_addr)
            nas_datas = []
            for nas in nass:
                nas_data = {c.name:getattr(nas, c.name) for c in nas.__table__.columns}
                nas_datas.append(nas_data)

            self.render_success(data=nas_datas)
        except Exception as err:
            logger.error(u'api fetch nas error, %s' % utils.safeunicode(traceback.format_exc()))
            self.render_unknow(err)