#!/usr/bin/env python
# coding=utf-8
import json
import re
import os
import urlparse
import urllib
import traceback
import tempfile
import functools
import base64
import time
import cyclone.web
from urllib import urlencode
from twisted.internet.threads import deferToThread
from toughradius.toughlib.storage import Storage
from toughradius.toughlib import utils, apiutils
from toughradius.toughlib.paginator import Paginator
from toughradius import __version__ as sys_version
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.common import tools
from toughradius.toughlib import redis_session
from toughradius.toughlib import dispatch, logger
from twisted.python.failure import Failure
from twisted.internet import reactor, defer
from cyclone import httpclient

class BaseHandler(cyclone.web.RequestHandler):

    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)
        self.aes = self.application.aes
        self.cache = self.application.mcache
        self.paycache = self.application.paycache
        self.mpsapi = self.application.mpsapi
        self.session = redis_session.Session(self.application.session_manager, self)
        self.wechat = self.application.wechat
        self.wxpay = self.application.wxpay
        self.wxpay_enable = int(self.get_param_value('mps_wxpay_enable', 0))

    def check_xsrf_cookie(self):
        pass

    def initialize(self):
        self.tp_lookup = self.application.tp_lookup
        self.db = self.application.db()

    def on_finish(self):
        self.db.close()

    def get_error_html(self, status_code, **kwargs):
        try:
            if 'exception' in kwargs:
                failure = kwargs.get('exception')
                logger.exception(failure)
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return self.render_json(code=1, msg=u'%s:服务器处理失败，请联系管理员' % status_code)
            if status_code == 404:
                return self.render_error(msg=u'404:页面不存在')
            if status_code == 403:
                return self.render_error(msg=u'403:非法的请求')
            if status_code == 500:
                return self.render_error(msg=u'500:服务器处理失败，请联系管理员')
            return self.render_error(msg=u'%s:服务器处理失败，请联系管理员' % status_code)
        except Exception as err:
            logger.exception(err)
            return self.render_error(msg=u'%s:服务器处理失败，请联系管理员' % status_code)

    def render(self, template_name, **template_vars):
        html = self.render_string(template_name, **template_vars)
        self.write(html)

    def render_error(self, **template_vars):
        tpl = 'error.html'
        html = self.render_string(tpl, **template_vars)
        self.write(html)

    def render_json(self, **template_vars):
        if not template_vars.has_key('code'):
            template_vars['code'] = 0
        resp = json.dumps(template_vars, ensure_ascii=False)
        self.write(resp)

    def render_string(self, template_name, **template_vars):
        template_vars['xsrf_form_html'] = self.xsrf_form_html
        template_vars['current_user'] = self.current_user
        template_vars['request'] = self.request
        template_vars['requri'] = '{0}://{1}'.format(self.request.protocol, self.request.host)
        template_vars['handler'] = self
        template_vars['utils'] = utils
        template_vars['tools'] = tools
        template_vars['sys_version'] = sys_version
        try:
            mytemplate = self.tp_lookup.get_template('mps/{0}'.format(template_name))
            return mytemplate.render(**template_vars)
        except Exception as err:
            logger.exception(err, trace='mps', func='base.render_string')
            raise

    def render_from_string(self, template_string, **template_vars):
        from mako.template import Template
        template = Template(template_string)
        return template.render(**template_vars)

    def get_params(self):
        arguments = self.request.arguments
        params = {}
        for k, v in arguments.items():
            if len(v) == 1:
                params[k] = v[0]
            else:
                params[k] = v

        return params

    def get_params_obj(self, obj):
        arguments = self.request.arguments
        for k, v in arguments.items():
            if len(v) == 1:
                if type(v[0]) == str:
                    setattr(obj, k, v[0].decode('utf-8', ''))
                else:
                    setattr(obj, k, v[0])
            elif type(v) == str:
                setattr(obj, k, v.decode('utf-8'))
            else:
                setattr(obj, k, v)

        return obj

    def get_param_value(self, name, defval = None):
        val = self.db.query(models.TrParam.param_value).filter_by(param_name=name).scalar()
        return val or defval

    def get_tpl_id(self, tpl_type):
        return self.db.query(models.TrContentTemplate.tpl_id).filter_by(tpl_type=tpl_type).scalar()

    def send_notify(self, oid, content):
        if not oid or not content:
            return
        func = lambda : self.wechat.send_text_message(oid, content)
        deferd = deferToThread(func)
        deferd.addErrback(logger.exception)