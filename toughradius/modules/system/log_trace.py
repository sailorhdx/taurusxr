#!/usr/bin/env python
# coding=utf-8
import cyclone.web
import decimal
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.customer import account
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.modules.settings import *
import functools

@permit.suproute('/admin/system/trace', u'系统日志查询', MenuSys, order=6.0002, is_menu=True)

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


@permit.suproute('/admin/user/trace', u'用户日志查询', MenuSys, order=6.0003, is_menu=True)

class UserTraceTraceHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('userlog_trace.html', keyword='', messages=[])

    @authenticated
    def post(self):
        keyword = self.get_argument('keyword', '')
        messages = self.logtrace.list_radius(keyword)
        self.render('userlog_trace.html', messages=messages, **self.get_params())