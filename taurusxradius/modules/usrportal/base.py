#!/usr/bin/env python
# coding=utf-8
import json
import urllib
import cyclone.web
import functools
import urlparse

import datetime
from cyclone.util import ObjectDict
from twisted.python.failure import Failure

from taurusxradius.common.alipay import AliPay, Settings
from taurusxradius.taurusxlib import utils
from taurusxradius.taurusxlib.paginator import Paginator
from taurusxradius import __version__ as sys_version
from taurusxradius.modules.settings import *
from taurusxradius.modules import models
from taurusxradius.common import tools
from taurusxradius.taurusxlib import redis_session
from taurusxradius.taurusxlib import logger

class BaseHandler(cyclone.web.RequestHandler):
    cache_key = 'taurusxradius.usrportal.'

    def __init__(self, *argc, **argkw):
        super(BaseHandler, self).__init__(*argc, **argkw)
        self.aes = self.application.aes
        self.cache = self.application.mcache
        self.paycache = self.application.paycache
        self.session = redis_session.Session(self.application.session_manager, self)
        self.lictype = os.environ.get('LICENSE_TYPE')

    @property
    def alipay(self):
        return AliPay(Settings(ALIPAY_INPUT_CHARSET='utf-8', ALIPAY_KEY=self.get_param_value('ALIPAY_KEY'),
                               ALIPAY_NOTIFY_URL=self.get_param_value('ALIPAY_NOTIFY_URL'),
                               ALIPAY_PARTNER=self.get_param_value('ALIPAY_PARTNER'),
                               ALIPAY_RETURN_URL=self.get_param_value('ALIPAY_RETURN_URL'),
                               ALIPAY_SELLER_EMAIL=self.get_param_value('ALIPAY_SELLER_EMAIL'), ALIPAY_SHOW_URL='',
                               ALIPAY_SIGN_TYPE='MD5', ALIPAY_TRANSPORT='https'), logger=logger)

    def initialize(self):
        self.tp_lookup = self.application.tp_lookup
        self.db = self.application.db()

    def on_finish(self):
        self.db.close()

    def get_error_html(self, status_code, **kwargs):
        try:
            if 'exception' in kwargs:
                failure = kwargs.get('exception')
                if isinstance(failure, cyclone.web.HTTPError):
                    failure = Failure(failure)
                logger.exception(failure)
                if os.environ.get('XDEBUG'):
                    from mako import exceptions
                    return exceptions.html_error_template().render(traceback=failure.getTracebackObject())
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
        template_vars['login_time'] = self.get_secure_cookie('tr_login_time')
        template_vars['request'] = self.request
        template_vars['requri'] = '{0}://{1}'.format(self.request.protocol, self.request.host)
        template_vars['handler'] = self
        template_vars['utils'] = utils
        template_vars['tools'] = tools
        template_vars['sys_version'] = sys_version
        mytemplate = self.tp_lookup.get_template('usrportal/{0}'.format(template_name))
        return mytemplate.render(**template_vars)

    def render_from_string(self, template_string, **template_vars):
        from mako.template import Template
        template = Template(template_string)
        return template.render(**template_vars)

    def render_alert(self, title, msg):
        self.render('alert.html', title=title, msg=msg)

    def get_page_data(self, query, page_size = 15):
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

    def set_session_user(self, uid, username, ipaddr, login_time, status, expire_date, create_time, product_policy, product_name):
        session_user = ObjectDict()
        session_user.uid = uid
        session_user.username = username
        session_user.ipaddr = ipaddr
        session_user.login_time = login_time
        session_user.status = status
        session_user.expire_date = expire_date
        session_user.create_time = create_time
        session_user.product_policy = product_policy
        session_user.product_name = product_name
        self.session['session_user'] = session_user
        self.session.save()
        return

    def clear_session(self):
        self.session.clear()
        self.clear_all_cookies()

    def get_current_user(self):
        return self.session.get('session_user')

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

    def get_product_attr(self, pid, name, attr_type = 0):
        return self.db.query(models.TrProductAttr).filter_by(product_id=pid, attr_name=name, attr_type=attr_type).first()

    def get_tpl_id(self, tpl_type):
        return self.db.query(models.TrContentTemplate.tpl_id).filter_by(tpl_type=tpl_type).scalar()

    def order_calc(self, product_id, old_expire = None):
        months = int(self.get_argument('months', 0))
        days = int(self.get_argument('days', 0))
        product = self.db.query(models.TrProduct).get(product_id)
        fee_value, expire_date = (None, None)
        if product.product_policy in (BOTimes, BOFlows): #买断时长，买断流量
            fee_value = utils.fen2yuan(product.fee_price)
            expire_date = MAX_EXPIRE_DATE
        elif product.product_policy == PPMonth: #预付费包月
            fee = decimal.Decimal(months) * decimal.Decimal(product.fee_price)
            fee_value = utils.fen2yuan(int(fee.to_integral_value()))
            start_expire = datetime.datetime.now()
            if old_expire:
                start_expire = datetime.datetime.strptime(old_expire, '%Y-%m-%d')
            expire_date = utils.add_months(start_expire, int(months), days=0)
            expire_date = expire_date.strftime('%Y-%m-%d')
        elif product.product_policy == PPDay: #预付费包日
            fee = decimal.Decimal(days) * decimal.Decimal(product.fee_price)
            fee_value = utils.fen2yuan(int(fee.to_integral_value()))
            start_expire = datetime.datetime.now()
            if old_expire:
                start_expire = datetime.datetime.strptime(old_expire, '%Y-%m-%d')
            expire_date = start_expire + datetime.timedelta(days=days)
            expire_date = expire_date.strftime('%Y-%m-%d')
        elif product.product_policy == BOMonth: #买断包月
            start_expire = datetime.datetime.now()
            if old_expire:
                start_expire = datetime.datetime.strptime(old_expire, '%Y-%m-%d')
            if months > 0 and months != product.fee_months:
                mprice = self.get_product_attr(product.id, 'month_price')
                if mprice and int(mprice.attr_value) > 0:
                    mpricefee = utils.yuan2fen(decimal.Decimal(mprice.attr_value))
                else:
                    mpricefee = decimal.Decimal(product.fee_price) / decimal.Decimal(product.fee_months)
                fee = decimal.Decimal(months) * mpricefee
                fee_value = utils.fen2yuan(int(fee.to_integral_value()))
                expire_date = utils.add_months(start_expire, int(months), days=0)
                expire_date = expire_date.strftime('%Y-%m-%d')
            else:
                fee_value = utils.fen2yuan(product.fee_price)
                expire_date = utils.add_months(start_expire, product.fee_months, days=0)
                expire_date = expire_date.strftime('%Y-%m-%d')
        elif product.product_policy == BODay: #买断包日
            start_expire = datetime.datetime.now()
            if old_expire:
                start_expire = datetime.datetime.strptime(old_expire, '%Y-%m-%d')
            if days > 0 and days != product.fee_days:
                dprice = self.get_product_attr(product.id, 'day_price')
                if dprice and int(dprice.attr_value) > 0:
                    dpricefee = utils.yuan2fen(decimal.Decimal(dprice.attr_value))
                else:
                    dpricefee = decimal.Decimal(product.fee_price) / decimal.Decimal(product.fee_days)
                fee = decimal.Decimal(days) * dpricefee
                fee_value = utils.fen2yuan(int(fee.to_integral_value()))
                expire_date = start_expire + datetime.timedelta(days=days)
                expire_date = expire_date.strftime('%Y-%m-%d')
            else:
                fee_value = utils.fen2yuan(product.fee_price)
                expire_date = start_expire + datetime.timedelta(days=product.fee_days)
                expire_date = expire_date.strftime('%Y-%m-%d')
        return (fee_value, expire_date)

def authenticated(method):

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                self.set_header('Content-Type', 'application/json; charset=UTF-8')
                self.write(json.dumps({'code': 1,
                 'msg': u'您的会话已过期，请重新登录！'}))
                return
            if self.request.method in ('GET', 'POST', 'HEAD'):
                return self.redirect('/usrportal/login')
            return self.render_error(msg=u'未授权的访问')
        else:
            return method(self, *args, **kwargs)

    return wrapper