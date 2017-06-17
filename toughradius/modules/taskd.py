#!/usr/bin/env python
# coding=utf-8
import sys
import os
import time
from twisted.internet import reactor, defer
from twisted.internet import protocol
from twisted.application import service, internet
from sqlalchemy.orm import scoped_session, sessionmaker
from toughradius.toughlib import logger, utils, dispatch
from toughradius.modules import models
from toughradius.toughlib.dbengine import get_engine
from toughradius.toughlib.config import redis_conf
from toughradius.toughlib.redis_cache import CacheManager
from toughradius.modules import tasks
from toughradius.modules import settings
from toughradius.modules import events
from toughradius.common import log_trace
from toughradius.common import eslogapi
import toughradius

class TaskDaemon:
    """
     定时任务管理守护进程
    """
    __taskclss__ = []

    def __init__(self, config = None, dbengine = None, **kwargs):
        self.config = config
        self.db_engine = dbengine or get_engine(config, pool_size=20)
        self.aes = kwargs.pop('aes', None)
        redisconf = redis_conf(config)
        self.cache = kwargs.pop('cache', CacheManager(redisconf, cache_name='RadiusTaskCache-%s' % os.getpid()))
        self.db = scoped_session(sessionmaker(bind=self.db_engine, autocommit=False, autoflush=False))
        self.load_tasks()
        if not kwargs.get('standalone'):
            logger.info('start register taskd events')
            dispatch.register(log_trace.LogTrace(redis_conf(config)), check_exists=True)
            if 'elasticsearch' in config:
                dispatch.register(eslogapi.EslogApi(config.elasticsearch))
            event_params = dict(dbengine=self.db_engine, mcache=self.cache, aes=self.aes)
            event_path = os.path.abspath(os.path.dirname(events.__file__))
            dispatch.load_events(event_path, 'toughradius.modules.events', event_params=event_params)
        return

    def process_task(self, task):
        r = task.process()
        if isinstance(r, defer.Deferred):
            cbk = lambda _time, _cbk, _task: reactor.callLater(_time, _cbk, _task)
            r.addCallback(cbk, self.process_task, task).addErrback(logger.exception)
        elif isinstance(r, (int, float)):
            reactor.callLater(r, self.process_task, task)

    def start(self):
        for taskcls in TaskDaemon.__taskclss__:
            task = taskcls(self)
            first_delay = task.first_delay()
            if first_delay:
                reactor.callLater(first_delay, self.process_task, task)
            else:
                self.process_task(task)
            logger.info('init task %s done' % task.__name__)

        logger.info('init task num : %s' % len(TaskDaemon.__taskclss__))

    def load_tasks(self):
        evs = set((os.path.splitext(it)[0] for it in os.listdir(os.path.dirname(tasks.__file__))))
        for ev in evs:
            try:
                __import__('toughradius.modules.tasks.%s' % ev)
            except Exception as err:
                logger.exception(err)
                continue


def run(config, dbengine = None, **kwargs):
    app = TaskDaemon(config, dbengine, **kwargs)
    app.start()