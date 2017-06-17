#!/usr/bin/env python
# coding=utf-8
import sys
import os
import time
import importlib
import cyclone.web
from cyclone import httpclient
from twisted.python import log
from twisted.internet import reactor
from twisted.application import service, internet
from mako.lookup import TemplateLookup
from sqlalchemy.orm import scoped_session, sessionmaker
from toughradius.toughlib import logger, utils, dispatch
from toughradius.modules import models
from toughradius.modules.ssportal import base
from toughradius.toughlib.dbengine import get_engine
from toughradius.toughlib.config import redis_conf
from toughradius.toughlib.permit import permit, load_events, load_handlers
from toughradius.modules.settings import *
from toughradius.toughlib.redis_cache import CacheManager
from toughradius.toughlib import redis_session
from toughradius.toughlib import dispatch
from toughradius.toughlib.dbutils import make_db
from toughradius.common import log_trace
from toughradius.common import eslogapi
import toughradius

class HttpServer(cyclone.web.Application):

    def __init__(self, config = None, dbengine = None, **kwargs):
        self.config = config
        os.environ['LICENSE_TYPE'] = 'taurusxee'
        settings = dict(cookie_secret='12oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=', login_url='/ssportal/login', template_path=os.path.join(os.path.dirname(toughradius.__file__), 'views'), static_path=os.path.join(os.path.dirname(toughradius.__file__), 'static'), xsrf_cookies=True, config=self.config, debug=self.config.system.debug, xheaders=True)
        self.tp_lookup = TemplateLookup(directories=[settings['template_path']], default_filters=['decode.utf8', 'h'], input_encoding='utf-8', output_encoding='utf-8', encoding_errors='ignore', module_directory='/var/taurusxr/free_module_ssportal')
        self.db_engine = dbengine or get_engine(config)
        self.db = scoped_session(sessionmaker(bind=self.db_engine, autocommit=False, autoflush=False))
        redisconf = redis_conf(config)
        self.logtrace = log_trace.LogTrace(redisconf)
        self.session_manager = redis_session.SessionManager(redisconf, settings['cookie_secret'], 3600)
        self.mcache = kwargs.get('cache', CacheManager(redisconf, cache_name='SspdCache-%s' % os.getpid()))
        self.paycache = CacheManager(redisconf, cache_name='SspdPayCache-%s' % os.getpid(), db=9)
        self.aes = kwargs.get('aes', utils.AESCipher(key=self.config.system.secret))
        logger.info('start register ssportal events')
        dispatch.register(self.mcache)
        dispatch.register(self.logtrace)
        if 'elasticsearch' in config:
            dispatch.register(eslogapi.EslogApi(config.elasticsearch))
        load_handlers(handler_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ssportal'), pkg_prefix='toughradius.modules.ssportal', excludes=['webserver', 'radius'])
        cyclone.web.Application.__init__(self, permit.all_handlers, **settings)

    def get_param_value(self, name, defval = None):
        db = self.db()
        try:
            val = db.query(models.TrParam.param_value).filter_by(param_name=name).scalar()
            return val or defval
        except:
            db.rollback()


def run(config, dbengine, **kwargs):
    app = HttpServer(config, dbengine)
    reactor.listenTCP(int(config.ssportal.port), app, interface=config.ssportal.host)