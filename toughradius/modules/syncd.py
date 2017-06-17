#!/usr/bin/env python
#coding:utf-8
import os
import six
import time
import json
import msgpack
import datetime
import toughradius
import traceback
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import defer
from toughradius.toughlib import utils
from toughradius.toughlib import mcache
from toughradius.toughlib import logger, dispatch
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.dbengine import get_engine
from toughradius.toughlib.config import redis_conf
from toughradius.toughlib.utils import timecast
from toughradius.modules import models
from toughradius.modules.settings import *
from toughradius.common import eslogapi
from toughradius.common import log_trace
from toughradius.toughlib.redis_cache import CacheManager
from collections import deque
from sqlalchemy import *
from sqlalchemy.sql import text as _sql
from txzmq import ZmqEndpoint, ZmqFactory, ZmqPushConnection, ZmqPullConnection, ZmqREPConnection, ZmqREQConnection

class DBSyncServer(object):
    """ 同步服务进程，接受其他服务器发送的同步数据，更新数据库
    """

    def __init__(self, config, dbengine, **kwargs):
        self.config = config
        self.que = deque()
        self.db_engine = dbengine or get_engine(config, pool_size=30)
        self.cache = CacheManager(redis_conf(config), cache_name='SyncdCache-%s' % os.getpid())
        self.metadata = models.get_metadata(self.db_engine)
        self.tables = {_name:_table for _name, _table in self.metadata.tables.items()}
        self.master_bind = ZmqREPConnection(ZmqFactory(), ZmqEndpoint('bind', config.ha.master))
        self.master_bind.gotMessage = self.dataReceived
        self.sync_task = HaSyncTask(config, self.db_engine, self.cache)
        self.ops = {'add': self.do_add,
         'update': self.do_update,
         'delete': self.do_delete}
        self.process()
        logger.info(u'启动HA同步服务: [Master] {} ～ [Slave] {}'.format(self.config.ha.master, self.config.ha.slave))
        if not kwargs.get('standalone'):
            self.logtrace = log_trace.LogTrace(redis_conf(config))
            if 'elasticsearch' in config:
                dispatch.register(eslogapi.EslogApi(config.elasticsearch))

    def key_where(self, objdata):
        """ 组装主键查询条件，只有同步的版本大于数据库的版本时才会更新
        """
        key_where = ' and '.join(("%s='%s'" % (k, v) for k, v in objdata.pkeys.items()))
        key_where = _sql(key_where)
        return key_where

    def do_add(self, objdata):
        """ 同步新增
        """
        if not objdata.pkeys or not isinstance(objdata.pkeys, dict):
            raise ValueError('pkeys error')
        dbtable = self.tables[objdata.table_name]
        key_where_sql = self.key_where(objdata)
        with self.db_engine.begin() as db:
            ret = db.execute(_sql('select count(*) from %s where %s' % (objdata.table_name, key_where_sql)))
            if ret.scalar() == 1:
                db.execute(dbtable.delete().where(key_where_sql))
            db.execute(dbtable.insert().values(objdata.content))

    def do_update(self, objdata):
        """ 同步更新，查询已经存在的数据并删除，重新插入
        """
        if not objdata.pkeys or not isinstance(objdata.pkeys, dict):
            return
        else:
            dbtable = self.tables[objdata.table_name]
            key_where_sql = self.key_where(objdata)
            with self.db_engine.begin() as db:
                ret = db.execute(_sql('select sync_ver from %s where %s' % (objdata.table_name, key_where_sql)))
                oldver = ret.scalar()
                if oldver is None:
                    db.execute(dbtable.insert().values(objdata.content))
                elif int(oldver) < int(objdata.sync_ver):
                    db.execute(dbtable.delete().where(key_where_sql))
                    db.execute(dbtable.insert().values(objdata.content))
            return

    def do_delete(self, objdata):
        """ 同步更新，查询已经存在的数据并删除
        """
        if not objdata.pkeys or not isinstance(objdata.pkeys, dict):
            return
        dbtable = self.tables[objdata.table_name]
        key_where_sql = self.key_where(objdata)
        with self.db_engine.begin() as db:
            db.execute(dbtable.delete().where(key_where_sql))

    def dataReceived(self, msgid, request):
        if 'HASYNC_DISABLE' in os.environ:
            return
        try:
            message = msgpack.unpackb(request)
            self.que.appendleft([msgid, Storage(message)])
        except:
            logger.error(traceback.print_exc())

    def process(self):
        try:
            msgid, objdata = self.que.pop()
            if objdata.action == 'ping':
                self.master_bind.reply(msgid, 'ping ok')
                reactor.callLater(0.005, self.process)
                return
        except:
            reactor.callLater(1, self.process)
            return

        try:
            table_name = objdata.table_name
            if table_name not in self.tables:
                self.reply(msgid, 1, u'数据库表 %s 不存在')
            else:
                opfunc = self.ops.get(objdata.action)
                if opfunc:
                    opfunc(objdata)
                    self.reply(msgid, 0, 'ok')
                else:
                    self.reply(msgid, 1, u'不支持的同步操作')
        except Exception as err:
            logger.exception(err)
            self.reply(msgid, 1, traceback.format_exc())
        finally:
            reactor.callLater(0.005, self.process)

    def reply(self, msgid, code, msg):
        try:
            data = msgpack.packb(dict(code=code, msg=msg))
            self.master_bind.reply(msgid, data)
        except Exception as e:
            logger.error(traceback.print_exc())


class HaSyncTask(object):
    """ 同步任务，定时查询需要同步的数据并向同步服务器发送
    """

    def __init__(self, config, db_engine, cache):
        self.config = config
        self.db_engine = db_engine
        self.cache = cache
        self.running = False
        self.ping_errs = 0
        self.syncer = ZmqREQConnection(ZmqFactory(), ZmqEndpoint('connect', self.config.ha.slave))
        self.repops = {0: self.do_succ,
         1: self.do_fail}
        reactor.callLater(1, self.ping)
        reactor.callLater(3, self.process)

    def do_succ(self, sync_id, **kwargs):
        try:
            with self.db_engine.begin() as db:
                table = models.TrRepliSyncStatus.__table__
                db.execute(models.TrRepliSyncStatus.__table__.delete().where(table.c.id == sync_id))
        except Exception as err:
            logger.error(traceback.format_exc())

    def do_fail(self, sync_id, msg = '', **kwargs):
        try:
            with self.db_engine.begin() as db:
                table = models.TrRepliSyncStatus.__table__
                stmt = table.update().where(table.c.id == sync_id).values(last_sync=utils.get_currtime(), sync_times=table.c.sync_times + 1, sync_status=2, error=utils.safeunicode(msg)[:2000])
                db.execute(stmt)
        except Exception as err:
            logger.error(traceback.format_exc())

    def on_reply(self, result, sync_id):
        try:
            reply = msgpack.unpackb(result[0])
            code, msg = reply['code'], reply['msg']
            self.repops[code](sync_id, msg=msg)
        except Exception as err:
            logger.error(traceback.format_exc())

    def on_fail(self, err, sync_id):
        self.do_fail(sync_id, msg=utils.safeunicode(err.getErrorMessage())[:2000])

    def ping(self):

        def onsucc(r):
            self.running = True
            self.ping_errs = 0
            self.cache.set(hadb_sync_status_cache_key, 0)
            logger.debug(u'同步链路检测成功:{}'.format(r[0]))

        def onfail(e):
            self.running = False
            self.ping_errs += 1
            self.cache.set(hadb_sync_status_cache_key, 1)
            logger.error(u'同步链路检测失败:{}'.format(repr(e)))

        def on_timeout(d):
            if not d.called:
                self.running = False
                self.ping_errs += 1
                self.cache.set(hadb_sync_status_cache_key, 2)
                logger.error(u'同步链路检测超时')

        try:
            d = self.syncer.sendMsg(msgpack.packb(dict(action='ping')))
            d.addCallbacks(onsucc, onfail)
            reactor.callLater(3.0, on_timeout, d)
        except:
            self.running = False
            traceback.print_exc()

        reactor.callLater(self.config.ha.get('ping_interval', 60), self.ping)

    def process(self):
        next_interval = self.config.ha.get('interval', 5)
        if not self.running:
            reactor.callLater(next_interval, self.process)
            return
        try:
            table = models.TrRepliSyncStatus.__table__
            with self.db_engine.begin() as conn:
                squery = conn.execute(table.select().where(table.c.sync_status.in_([0, 2])).where(table.c.sync_times < 5))
                count = squery.rowcount
                self.cache.set(hadb_sync_count_cache_key, count)
                if count == 0:
                    reactor.callLater(next_interval, self.process)
                    return
                if count > 100:
                    next_interval = 1.0
                logger.info(u'等待同步数据记录数:{}'.format(count))
                _total = 0
                for _status in squery.fetchmany(size=100):
                    try:
                        statobj = Storage()
                        statobj.id = _status[table.c.id]
                        statobj.table_name = _status[table.c.table_name]
                        statobj.action = _status.action
                        statobj.pkeys = json.loads(_status[table.c.pkeys])
                        statobj.content = json.loads(_status[table.c.content])
                        statobj.sync_ver = _status[table.c.sync_ver]
                        message = msgpack.packb(statobj)
                        d = self.syncer.sendMsg(message)
                        d.addCallback(self.on_reply, statobj.id)
                        d.addErrback(self.on_fail, statobj.id)
                        _total += 1
                    except Exception as err:
                        logger.error(traceback.format_exc())

        except Exception as err:
            logger.error(traceback.format_exc())

        reactor.callLater(next_interval, self.process)


def run(config, dbengine = None, **kwargs):
    if 'ha' not in config or config.ha.get('enable') == 0:
        logger.info('HA同步服务未启用')
    else:
        DBSyncServer(config, dbengine, **kwargs)