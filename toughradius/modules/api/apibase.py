#!/usr/bin/env python
# coding=utf-8
import os
import json
import time
import traceback
import functools
from hashlib import md5
from cyclone.util import ObjectDict
from toughradius.toughlib import utils, apiutils, dispatch, logger
from toughradius.modules.base import BaseHandler
from toughradius.toughlib.apiutils import apistatus

class ApiHandler(BaseHandler):

    def check_xsrf_cookie(self):
        pass

    def render_result(self, **result):
        resp = apiutils.make_message(self.settings.config.system.secret, **result)
        if self.settings.debug:
            logger.debug('[api debug] :: %s response body: %s' % (self.request.path, utils.safeunicode(resp)))
        self.write(resp)

    def parse_form_request(self):
        try:
            return apiutils.parse_form_request(self.settings.config.system.secret, self.get_params())
        except Exception as err:
            logger.error(u'api authorize parse error, %s' % utils.safeunicode(traceback.format_exc()))
            self.render_parse_err(err, msg=u'ParseRequest Error: %s' % utils.safeunicode(err.message))
            return None

        return None

    def get_current_user(self):
        session_opr = ObjectDict()
        session_opr.username = 'api'
        session_opr.ipaddr = self.request.remote_ip
        session_opr.opr_type = 0
        session_opr.login_time = utils.get_currtime()
        return session_opr

    def _decode_msg(self, err, msg):
        _msg = msg and utils.safeunicode(msg) or ''
        if issubclass(type(err), BaseException):
            return u'{0}, {1}'.format(utils.safeunicode(_msg), utils.safeunicode(err.message))
        else:
            return _msg

    def render_success(self, msg = None, **result):
        self.render_result(code=apistatus.success.code, msg=self._decode_msg(None, msg or apistatus.success.msg), **result)
        return

    def render_sign_err(self, err = None, msg = None):
        self.render_result(code=apistatus.sign_err.code, msg=self._decode_msg(err, msg or apistatus.sign_err.msg))

    def render_parse_err(self, err = None, msg = None):
        self.render_result(code=apistatus.sign_err.code, msg=self._decode_msg(err, msg or apistatus.sign_err.msg))

    def render_verify_err(self, err = None, msg = None):
        self.render_result(code=apistatus.verify_err.code, msg=self._decode_msg(err, msg or apistatus.verify_err.msg))

    def render_server_err(self, err = None, msg = None):
        self.render_result(code=apistatus.server_err.code, msg=self._decode_msg(err, msg or apistatus.server_err.msg))

    def render_timeout(self, err = None, msg = None):
        self.render_result(code=apistatus.timeout.code, msg=self._decode_msg(err, msg or apistatus.timeout))

    def render_limit_err(self, err = None, msg = None):
        self.render_result(code=apistatus.limit_err.code, msg=self._decode_msg(err, msg or apistatus.limit_err))

    def render_unknow(self, err = None, msg = None):
        self.render_result(code=apistatus.unknow.code, msg=self._decode_msg(err, msg or apistatus.unknow))


def authapi(method):

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        allows = os.environ.get('AllowIps')
        if allows and self.request.remote_ip not in allows:
            return self.render_json(msg=u'未授权的访问IP来源')
        if int(self.get_param_value('system_api_enable', '0')) == 0:
            return self.render_json(msg=u'未授权的访问API调用')
        return method(self, *args, **kwargs)

    return wrapper