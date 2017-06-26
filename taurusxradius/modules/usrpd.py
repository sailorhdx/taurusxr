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
from taurusxradius.taurusxlib import logger, utils, dispatch
from taurusxradius.modules import models
from taurusxradius.modules.ssportal import base
from taurusxradius.taurusxlib.dbengine import get_engine
from taurusxradius.taurusxlib.config import redis_conf
from taurusxradius.taurusxlib.permit import permit, load_events, load_handlers
from taurusxradius.modules.settings import *
from taurusxradius.taurusxlib.redis_cache import CacheManager
from taurusxradius.taurusxlib import redis_session
from taurusxradius.taurusxlib import dispatch
from taurusxradius.taurusxlib.dbutils import make_db
from taurusxradius.common import log_trace
from taurusxradius.common import eslogapi
import taurusxradius

class HttpServer(cyclone.web.Application):

    def __init__(self, config = None, dbengine = None, **kwargs):
        self.config = config
        os.environ['LICENSE_TYPE'] = 'taurusxee'
        settings = dict(cookie_secret='12oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=', login_url='/usrportal/login', template_path=os.path.join(os.path.dirname(taurusxradius.__file__), 'views'), static_path=os.path.join(os.path.dirname(taurusxradius.__file__), 'static'), xsrf_cookies=True, config=self.config, debug=self.config.system.debug, xheaders=True)
        self.tp_lookup = TemplateLookup(directories=[settings['template_path']], default_filters=['decode.utf8', 'h'], input_encoding='utf-8', output_encoding='utf-8', encoding_errors='ignore', module_directory='/var/taurusxr/usrportal')
        self.db_engine = dbengine or get_engine(config)
        self.db = scoped_session(sessionmaker(bind=self.db_engine, autocommit=False, autoflush=False))
        redisconf = redis_conf(config)
        self.logtrace = log_trace.LogTrace(redisconf)
        self.session_manager = redis_session.SessionManager(redisconf, settings['cookie_secret'], 3600)
        self.mcache = kwargs.get('cache', CacheManager(redisconf, cache_name='UsrpdCache-%s' % os.getpid()))
        self.paycache = CacheManager(redisconf, cache_name='UsrpdPayCache-%s' % os.getpid(), db=9)
        self.aes = kwargs.get('aes', utils.AESCipher(key=self.config.system.secret))
        logger.info('start register usrportal events')
        dispatch.register(self.mcache)
        dispatch.register(self.logtrace)
        if 'elasticsearch' in config:
            dispatch.register(eslogapi.EslogApi(config.elasticsearch))
        load_handlers(handler_path=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'usrportal'), pkg_prefix='taurusxradius.modules.usrportal', excludes=['webserver', 'radius'])
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
    reactor.listenTCP(int(config.usrportal.port), app, interface=config.usrportal.host)