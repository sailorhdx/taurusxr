#!/usr/bin/env python
# coding=utf-8
import time
import traceback
from toughradius.toughlib import utils, apiutils, dispatch, logger
from toughradius.toughlib.permit import permit
from toughradius.modules.api.apibase import ApiHandler
from toughradius.modules.api.apibase import authapi
from toughradius.modules import models
from toughradius.modules.dbservice.customer_add import CustomerAdd

@permit.route('/api/v1/customer/add')

class CustomerAddApiHandler(ApiHandler):

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            if not formdata:
                return
            service = CustomerAdd(self.db, self.aes)
            ret = service.add(formdata)
            if ret:
                return self.render_success()
            return self.render_server_err(msg=service.last_error)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)