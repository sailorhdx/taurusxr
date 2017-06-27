#!/usr/bin/env python
# coding=utf-8
import sys
import os
import time
import json
import base64
import cyclone.web
import traceback
import datetime
import uuid
from hashlib import md5
from twisted.python import log
from twisted.internet import reactor
from twisted.application import service, internet
from mako.lookup import TemplateLookup
from sqlalchemy.orm import scoped_session, sessionmaker
from taurusxradius.taurusxlib import logger, utils, dispatch, storage
from taurusxradius.modules import models
from taurusxradius.modules import base
from taurusxradius.taurusxlib.dbengine import get_engine
from taurusxradius.taurusxlib.config import redis_conf
from taurusxradius.taurusxlib.permit import permit, load_events, load_handlers
from taurusxradius.modules.settings import *
from taurusxradius.taurusxlib.redis_cache import CacheManager
from taurusxradius.taurusxlib import redis_session
from taurusxradius.taurusxlib import dispatch
from taurusxradius.taurusxlib.db_backup import DBBackup
from taurusxradius.common import log_trace
from taurusxradius.common import eslogapi
from taurusxradius.common import mpsapi
from taurusxradius.common import tools
from wechat_sdk import WechatBasic, WechatConf
from taurusxradius import upgrade
import taurusxradius
import functools

class HttpServer(cyclone.web.Application):

    def __init__(self, config = None, dbengine = None, **kwargs):
        self.config = config
        settings = dict(cookie_secret='12oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=', login_url='/admin/login', template_path=os.path.join(os.path.dirname(taurusxradius.__file__), 'views'), static_path=os.path.join(os.path.dirname(taurusxradius.__file__), 'static'), xsrf_cookies=True, config=self.config, debug=self.config.system.debug, xheaders=True)
        self.tp_lookup = TemplateLookup(directories=[settings['template_path']], default_filters=['decode.utf8', 'h'], input_encoding='utf-8', output_encoding='utf-8', encoding_errors='ignore', module_directory='/var/taurusxr/free_module_manage')
        self.license = storage.Storage(dict(sid=tools.get_sys_uuid(), type='taurusxee', create_at='2017-01-01', expire='3000-12-30'))
        os.environ['LICENSE_TYPE'] = 'taurusxee'
        self.db_engine = dbengine or get_engine(config)
        self.db = scoped_session(sessionmaker(bind=self.db_engine, autocommit=False, autoflush=False))
        redisconf = redis_conf(config)
        self.logtrace = log_trace.LogTrace(redisconf)
        self.session_manager = redis_session.SessionManager(redisconf, settings['cookie_secret'], 3600)
        self.mcache = kwargs.get('cache', CacheManager(redisconf, cache_name='RadiusManageCache-%s' % os.getpid()))
        batchsize = 32 if self.config.database.dbtype == 'sqlite' else 500
        self.db_backup = DBBackup(models.get_metadata(self.db_engine), excludes=['tr_online',
         'system_session',
         'system_cache',
         'tr_ticket',
         'tr_billing'], batchsize=batchsize)
        self.aes = kwargs.get('aes', utils.AESCipher(key=self.config.system.secret))
        self.init_superrpc()
        dispatch.register(self.mcache)
        dispatch.register(self.logtrace)
        if 'elasticsearch' in self.config:
            dispatch.register(eslogapi.EslogApi(self.config.elasticsearch))
        self.mpsapi = None
        self.wechat = None
        self.init_handlers()
        self.init_events()
        cyclone.web.Application.__init__(self, permit.all_handlers, **settings)
        return

    def init_superrpc(self):
        """ 初始化进程管理器
        """
        self.superrpc = None
        if self.config.system.get('superrpc'):
            try:
                import xmlrpclib
                self.superrpc = xmlrpclib.Server(self.config.system.superrpc)
                os.environ['TAURUSXEE_SUPER_RPC'] = 'true'
            except:
                logger.error(traceback.format_exc())

        return

    def init_handlers(self):
        """ 初始化web控制器
        """
        handler_path = os.path.abspath(os.path.dirname(__file__))
        excludes = ['ssportal',
                    'usrportal',
         'webserver',
         'radius',
         'mps',
         'wechat',
         'wlanportal',
         'hgboss',
        # 'agency',
        # 'busstat',
         'wlan']
        load_handlers(handler_path=handler_path, pkg_prefix='taurusxradius.modules', excludes=excludes)

    def init_events(self):
        """ 初始化事件
        """
        event_params = dict(dbengine=self.db_engine, mcache=self.mcache, aes=self.aes, wechat=self.wechat)
        event_path = os.path.abspath(os.path.dirname(taurusxradius.modules.events.__file__))
        dispatch.load_events(event_path, 'taurusxradius.modules.events', event_params=event_params)

    def start_install(self, settings):
        """ 初始化授权吗安装服务
        """
        logger.info('Start install service')
        from twisted.internet._signals import installHandler
        cyclone.web.Application.__init__(self, [('/', installHandler)], **settings)

    def get_param_value(self, name, defval = None):

        def fetch_result():
            table = models.TrParam.__table__
            with self.db_engine.begin() as conn:
                return conn.execute(table.select().with_only_columns([table.c.param_value]).where(table.c.param_name == name)).scalar() or defval

        try:
            return self.mcache.aget(param_cache_key(name), fetch_result, expire=600)
        except Exception as err:
            logger.exception(err)
            return defval


def run(config, dbengine, **kwargs):
    app = HttpServer(config, dbengine)
    reactor.listenTCP(int(config.admin.port), app, interface=config.admin.host)