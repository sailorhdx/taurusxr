#!/usr/bin/env python
# coding=utf-8
import json
import re
import time
import urlparse
import urllib
import traceback
import functools
import cyclone.web
from hashlib import md5
from mako.template import Template
from cyclone.util import ObjectDict
from twisted.internet import defer
from toughradius.toughlib import utils, apiutils
from toughradius.toughlib import dispatch, logger
from toughradius.toughlib.storage import Storage
from toughradius.modules import models
from toughradius.toughlib import db_session as session
from toughradius.modules import settings

class BaseHandler(cyclone.web.RequestHandler):

    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)
        self.cache = self.application.mcache
        self.aes = self.application.aes
        self.session = session.Session(self.application.session_manager, self)

    def check_xsrf_cookie(self):
        pass

    def initialize(self):
        self.tp_lookup = self.application.tp_lookup
        self.db = self.application.db()

    def on_finish(self):
        self.db.close()

    def get_error_html(self, status_code = 500, **kwargs):
        logger.info('http error : [status_code:{0}], {1}'.format(status_code, utils.safestr(kwargs)))
        if status_code == 404:
            return self.render_string('error.html', msg=u'404:页面不存在')
        elif status_code == 403:
            return self.render_string('error.html', msg=u'403:非法的请求')
        elif status_code == 500:
            return self.render_string('error.html', msg=u'500:服务器处理失败，请联系管理员')
        else:
            return self.render_string('error.html', msg=u'%s:服务器处理失败，请联系管理员' % status_code)

    def render(self, template_name, **template_vars):
        html = self.render_string(template_name, **template_vars)
        self.write(html)

    def render_error(self, **template_vars):
        logger.info('render template error: {0}'.format(repr(template_vars)))
        tpl_name = template_vars.get('tpl_name', '')
        tpl = self.get_error_template(tpl_name)
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
        template_vars['login_time'] = self.get_secure_cookie('portal_logintime')
        template_vars['request'] = self.request
        template_vars['requri'] = '{0}://{1}'.format(self.request.protocol, self.request.host)
        template_vars['handler'] = self
        template_vars['utils'] = utils
        try:
            mytemplate = self.tp_lookup.get_template('wlanportal/%s' % template_name)
            return mytemplate.render(**template_vars)
        except Exception as err:
            logger.info('Render template error {0}'.format(utils.safestr(err)))
            raise

    def render_from_string(self, template_string, **template_vars):
        template = Template(template_string)
        return template.render(**template_vars)

    def set_session_user(self, username, ipaddr, login_time, **kwargs):
        session_user = ObjectDict()
        session_user.username = username
        session_user.ipaddr = ipaddr
        session_user.macaddr = kwargs.pop('macaddr', '')
        session_user.login_time = login_time
        session_user.update(**kwargs)
        self.session['wlan_session_user'] = session_user
        self.session.save()

    def clear_session(self):
        self.session.clear()
        self.session.save()
        self.clear_all_cookies()

    def set_remerber_user(self, user, pwd):
        self.session['toughee_wlan_user'] = user
        self.session['toughee_wlan_pwd'] = pwd
        self.session.save()

    def get_remember_user(self):
        user = self.session.get('toughee_wlan_user')
        pwd = self.session.get('toughee_wlan_pwd')
        return (user, pwd)

    def get_current_user(self):
        return self.session.get('wlan_session_user')

    def get_wlan_params(self, query_str):
        query_str = urllib.unquote(query_str)
        params = urlparse.parse_qs(query_str)
        param_dict = {k:params[k][0] for k in params}
        return param_dict

    def get_portal_name(self):
        return self.get_param_value('wlan_portal_name', u'无线认证')

    def get_login_template(self, tpl_name = None):
        if tpl_name:
            return '%s/login.html' % tpl_name
        else:
            return 'default/login.html'

    def get_error_template(self, tpl_name = None):
        if tpl_name:
            return '%s/error.html' % tpl_name
        else:
            return 'default/error.html'

    def get_index_template(self, tpl_name = None):
        if tpl_name:
            return '%s/index.html' % tpl_name
        else:
            return 'default/index.html'

    def get_template_attrs(self, ssid):
        """ 获取模版信息，支持缓存
        """

        def fetch_result():
            domain_code = self.db.query(models.TrDomainAp.domain_code).filter_by(ssid=ssid).scalar()
            tpl_name = self.db.query(models.TrDomain.tpl_name).filter_by(domain_code=domain_code).scalar()
            tpl_name = tpl_name or 'default'
            print ssid, domain_code
            tplattrs = Storage(tpl_path=tpl_name, ssid=ssid, domain=domain_code)
            dmattrs = self.db.query(models.TrDomainAttr).filter_by(domain_code=domain_code)
            for dattr in dmattrs:
                tplattrs[dattr.attr_name] = dattr.attr_value

            return tplattrs

        return fetch_result()

    def get_nas(self, ipaddr, nasid = None):
        """ 获取AC接入设备信息，支持缓存
        """

        def fetch_result():
            nas = self.db.query(models.TrBas).filter_by(ip_addr=ipaddr).first()
            if not nas:
                nas = self.db.query(models.TrBas).filter_by(nas_id=nasid).first()
            return nas and {c.name:getattr(nas, c.name) for c in nas.__table__.columns} or {}

        return self.cache.aget(settings.bas_cache_ipkey(ipaddr), fetch_result, expire=600)

    def get_domain(self, ssid):
        """ 获取认证域信息，支持缓存
        """

        def fetch_result():
            return self.db.query(models.TrDomainAp.domain_code).filter_by(ssid=ssid).scalar()

        return self.cache.aget(settings.wlan_domain_cache_key(ssid), fetch_result, expire=600)

    def get_param_value(self, name, defval = None):
        val = self.db.query(models.TrParam.param_value).filter_by(param_name=name).scalar()
        return val or defval