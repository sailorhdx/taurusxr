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
        os.environ['LICENSE_TYPE'] = 'taurusxee'
        settings = dict(cookie_secret='12oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=', login_url='/wlanportal/default/login', template_path=os.path.join(os.path.dirname(taurusxradius.__file__), 'views'), static_path=os.path.join(os.path.dirname(taurusxradius.__file__), 'static'), xsrf_cookies=True, config=self.config, debug=self.config.system.debug, xheaders=True)
        self.tp_lookup = TemplateLookup(directories=[settings['template_path']], default_filters=['decode.utf8', 'h'], input_encoding='utf-8', output_encoding='utf-8', encoding_errors='ignore', module_directory='/var/taurusxr/free_module_manage')
        self.db_engine = dbengine or get_engine(config)
        self.db = scoped_session(sessionmaker(bind=self.db_engine, autocommit=False, autoflush=False))
        redisconf = redis_conf(config)
        self.logtrace = log_trace.LogTrace(redisconf)
        self.session_manager = redis_session.SessionManager(redisconf, settings['cookie_secret'], 3600)
        self.mcache = kwargs.get('cache', CacheManager(redisconf, cache_name='RadiusManageCache-%s' % os.getpid()))
        self.aes = kwargs.get('aes', utils.AESCipher(key=self.config.system.secret))
        logger.info('start register wlanportal events')
        dispatch.register(self.mcache)
        dispatch.register(self.logtrace)
        if 'elasticsearch' in self.config:
            dispatch.register(eslogapi.EslogApi(self.config.elasticsearch))
        load_handlers(handler_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'wlanportal'), pkg_prefix='taurusxradius.modules.wlanportal', excludes=['webserver', 'radius'])
        cyclone.web.Application.__init__(self, permit.all_handlers, **settings)
        return

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
    reactor.listenTCP(int(config.portal.port), app, interface=config.portal.host)