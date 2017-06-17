#!/usr/bin/env python
# coding=utf-8
import json
import re
import urlparse
import urllib
import cyclone.web
import tempfile
import traceback
import functools
import urlparse
from urllib import urlencode
from cyclone.util import ObjectDict
from toughradius.toughlib import utils
from toughradius.toughlib.paginator import Paginator
from toughradius import __version__ as sys_version
from toughradius.toughlib.permit import permit
from toughradius.modules.settings import *
from toughradius.modules import models
from toughradius.common import tools, alipay
from toughradius.toughlib import redis_session
from toughradius.toughlib import dispatch, logger

class BaseHandler(cyclone.web.RequestHandler):
    cache_key = 'toughradius.admin.'

    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)
        self.aes = self.application.aes
        self.cache = self.application.mcache
        self.db_backup = self.application.db_backup
        self.logtrace = self.application.logtrace
        self.superrpc = self.application.superrpc
        self.mpsapi = self.application.mpsapi
        self.wechat = self.application.wechat
        self.license = self.application.license
        self.session = redis_session.Session(self.application.session_manager, self)

    def check_xsrf_cookie(self):
        if self.settings.config.system.get('production'):
            return super(BaseHandler, self).check_xsrf_cookie()

    def initialize(self):
        self.tp_lookup = self.application.tp_lookup
        self.db = self.application.db()

    def on_finish(self):
        self.db.close()

    def get_error_html(self, status_code = 500, **kwargs):
        if 'exception' in kwargs:
            failure = kwargs.get('exception')
            print type(failure), dir(failure)
            logger.exception(failure)
            if os.environ.get('XDEBUG'):
                from mako import exceptions
                return exceptions.html_error_template().render(traceback=failure.getTracebackObject())
        try:
            logger.error('HTTPError : {0} [status_code:{1}], {2}'.format(self.request.path, status_code, repr(kwargs)), tag='manage_handler_error')
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return self.render_json(code=1, msg=u'%s:服务器处理失败，请联系管理员' % status_code)
            if status_code == 404:
                return self.render_string('error.html', msg=u'404:页面不存在')
            if status_code == 403:
                return self.render_string('error.html', msg=u'403:非法的请求')
            if status_code == 500:
                return self.render_string('error.html', msg=u'500:服务器处理失败，请联系管理员')
            return self.render_string('error.html', msg=u'%s:服务器处理失败，请联系管理员' % status_code)
        except Exception as err:
            logger.exception(err, tag='manage_handler_error')
            return self.render_string('error.html', msg=u'%s:服务器处理失败，请联系管理员' % status_code)

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
        template_vars['login_time'] = self.get_secure_cookie('tr_login_time')
        template_vars['request'] = self.request
        template_vars['requri'] = '{0}://{1}'.format(self.request.protocol, self.request.host)
        template_vars['handler'] = self
        template_vars['utils'] = utils
        template_vars['tools'] = tools
        template_vars['sys_version'] = sys_version
        template_vars['sysenv'] = os.environ
        if self.current_user:
            template_vars['permit'] = self.current_user.permit
            template_vars['menu_icons'] = MENU_ICONS
            template_vars['all_menus'] = self.current_user.permit.build_menus(order_cats=ADMIN_MENUS)
        mytemplate = self.tp_lookup.get_template('admin/{0}'.format(template_name))
        return mytemplate.render(**template_vars)

    def render_from_string(self, template_string, **template_vars):
        from mako.template import Template
        template = Template(template_string)
        return template.render(**template_vars)

    def get_page_data(self, query, page_size = 15):
        if not page_size:
            page_size = self.application.settings.get('page_size', 15)
        page = int(self.get_argument('page', 1))
        offset = (page - 1) * page_size
        result = query.limit(page_size).offset(offset)
        page_data = Paginator(self.get_page_url, page, query.count(), page_size)
        page_data.result = result
        return page_data

    def get_page_url(self, page, form_id = None):
        if form_id:
            return "javascript:goto_page('%s',%s);" % (form_id.strip(), page)
        path = self.request.path
        query = self.request.query
        qdict = urlparse.parse_qs(query)
        for k, v in qdict.items():
            if isinstance(v, list):
                qdict[k] = v and v[0] or ''

        qdict['page'] = page
        return path + '?' + urllib.urlencode(qdict)

    def set_session_user(self, username, ipaddr, opr_type, login_time):
        session_opr = ObjectDict()
        session_opr.operator_name = username
        session_opr.username = username
        session_opr.operate_ip = ipaddr
        session_opr.ipaddr = ipaddr
        session_opr.opr_type = opr_type
        session_opr.login_time = login_time
        session_opr.resources = [ r.rule_path for r in self.db.query(models.TrOperatorRule).filter_by(operator_name=username) ]
        _agency = self.db.query(models.TrAgency).filter_by(operator_name=username).first()
        session_opr.agency_id = _agency.id if _agency else None
        session_opr.agency_name = _agency.agency_name if _agency else None
        self.session['session_opr'] = session_opr
        self.session.save()
        return

    def clear_session(self):
        self.session.clear()
        self.clear_all_cookies()

    def get_current_user(self):
        opr = self.session.get('session_opr')
        if opr:
            opr.permit = permit.fork(opr.username, opr.opr_type, opr.resources)
        return opr

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

    def get_opr_products(self):
        opr_type = int(self.current_user.opr_type)
        if opr_type == 0:
            return self.db.query(models.TrProduct).filter(models.TrProduct.product_status == 0)
        else:
            return self.db.query(models.TrProduct).filter(models.TrProduct.id == models.TrOperatorProducts.product_id, models.TrOperatorProducts.operator_name == self.current_user.username, models.TrProduct.product_status == 0)

    def get_opr_nodes(self):
        opr_type = int(self.current_user.opr_type)
        if opr_type == 0:
            return self.db.query(models.TrNode)
        opr_name = self.current_user.username
        return self.db.query(models.TrNode).filter(models.TrNode.id == models.TrOperatorNodes.node_id, models.TrOperatorNodes.operator_name == opr_name)

    def get_opr_agencies(self):
        opr_type = int(self.current_user.opr_type)
        if opr_type == 0:
            return self.db.query(models.TrAgency)
        opr_name = self.current_user.username
        return self.db.query(models.TrAgency).filter(models.TrAgency.operator_name == opr_name)

    def get_opr_areas(self):
        opr_type = int(self.current_user.opr_type)
        if opr_type == 0:
            return self.db.query(models.TrNode.node_name, models.TrArea).filter(models.TrNode.id == models.TrArea.node_id)
        opr_name = self.current_user.username
        return self.db.query(models.TrNode.node_name, models.TrArea).filter(models.TrNode.id == models.TrOperatorNodes.node_id, models.TrOperatorNodes.operator_name == opr_name, models.TrNode.id == models.TrArea.node_id)

    def get_param_value(self, name, defval = None):
        val = self.db.query(models.TrParam.param_value).filter_by(param_name=name).scalar()
        return val or defval

    def get_license_ulimit(self, ulimit):
        if not ulimit:
            if self.license.get('type') in 'taurusxee' or '-oem' in self.license.get('type'):
                return 100000
            elif self.license.get('type') in 'community':
                return 5000
            elif self.license.get('type') in 'evaluation':
                return 128
            else:
                return 1000
        else:
            return int(ulimit)

    def add_oplog(self, message):
        ops_log = models.TrOperateLog()
        ops_log.id = utils.get_uuid()
        ops_log.operator_name = self.current_user.username
        ops_log.operate_ip = self.current_user.ipaddr
        ops_log.operate_time = utils.get_currtime()
        ops_log.operate_desc = message
        ops_log.sync_ver = tools.gen_sync_ver()
        self.db.add(ops_log)

    def export_file(self, filename, data):
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=' + filename)
        self.write(data.xls)
        self.finish()

    def send_wechat_notify(self, openid, message):
        if openid and message:
            from twisted.internet.iocpreactor import reactor
            reactor.callLater(1.0, self.wechat.send_text_message, openid, message)


class PageNotFoundHandler(BaseHandler):

    def get(self):
        self.send_error(404)


def authenticated(method):

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        allows = os.environ.get('AllowIps')
        if allows and self.request.remote_ip not in allows:
            return self.render_error(msg=u'未授权的访问IP来源')
        elif not self.current_user:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                self.set_header('Content-Type', 'application/json; charset=UTF-8')
                self.write(json.dumps({'code': 1,
                 'msg': u'您的会话已过期，请重新登录！'}))
                return
            if self.request.method in ('GET', 'POST', 'HEAD'):
                url = self.get_login_url()
                if '?' not in url:
                    if urlparse.urlsplit(url).scheme:
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    url += '?' + urlencode(dict(next=next_url))
                self.redirect(url)
                return
            return self.render_error(msg=u'未授权的访问')
        elif not self.current_user.permit.match(self.current_user.username, self.request.path):
            return self.render_error(msg=u'未授权的访问')
        else:
            return method(self, *args, **kwargs)

    return wrapper