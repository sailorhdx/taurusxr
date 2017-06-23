#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
from taurusxradius.modules import models
from taurusxradius.modules.base import BaseHandler, authenticated
from taurusxradius.modules.customer import account
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, dispatch, db_cache
from taurusxradius.modules.settings import *

@permit.route('/admin/system/trace', u'系统消息跟踪', MenuSys, order=6.00002, is_menu=True)

class SystemTraceTraceHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('log_trace.html', keyword='', messages=[])

    @authenticated
    def post(self):
        msg_type = self.get_argument('msg_type', '')
        keyword = self.get_argument('keyword', '')
        messages = []
        if msg_type == 'radius':
            messages = self.logtrace.list_radius(keyword)
        else:
            messages = (m for m in self.logtrace.list_trace(msg_type) if keyword in m)
        self.render('log_trace.html', messages=messages, **self.get_params())