#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.toughlib import utils, dispatch
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib import logger
from toughradius.modules import models
from toughradius.modules.events.event_basic import BasicEvent
from toughradius.modules.events.routeros_event import RouterOSSyncEvent
from toughradius.common import tools
from twisted.internet import reactor

class RouterOSPoolSyncEvent(RouterOSSyncEvent):

    def event_rossync_resync_pool(self, bas_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        try:
            logger.info('resync pool: bas_id={0}'.format(bas_id))
            rcli = self.get_bas_ros(bas_id)

            def update_pools(poolresp, name, ranges, next_pool):
                if poolresp and '!re' not in poolresp[0]:
                    d = rcli.add_pool(name, ranges, next_pool)
                    d.addCallback(self.onresp, 'add pool', rcli.apiaddr)
                    d.addErrback(self.onerror, 'add pool', rcli.apiaddr)
                else:
                    d2 = rcli.set_pool(name, ranges, next_pool)
                    d2.addCallback(self.onresp, 'set pool', rcli.apiaddr)
                    d2.addErrback(self.onerror, 'set pool', rcli.apiaddr)

            with make_db(self.db) as db:
                for p in self.db.query(models.TrAddrPool).all():
                    dg = rcli.get_pool(p.pool_name)
                    dg.addCallback(update_pools, p.pool_name, '%s-%s' % (p.start_ip, p.end_ip), p.next_pool)
                    dg.addErrback(self.onerror, 'get pool', rcli.apiaddr)

        except Exception as err:
            logger.exception(err)

    def event_rossync_add_pool(self, name, ranges, next_pool = None, bas_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        logger.info('add pool: name={0}, {1} {2}'.format(name, ranges, next_pool))
        allros = []
        if bas_id:
            allros.append(self.get_bas_ros(bas_id))
        else:
            allros = self.get_all_ros()
        for rcli in allros:
            d = rcli.add_pool(name, ranges, next_pool)
            d.addCallback(self.onresp, 'add pool', rcli.apiaddr)
            d.addErrback(self.onerror, 'add pool', rcli.apiaddr)

    def event_rossync_set_pool(self, name, ranges = None, next_pool = None, bas_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        logger.info('set pool: name={0}, {1} {2}'.format(name, ranges, next_pool))
        allros = []
        if bas_id:
            allros.append(self.get_bas_ros(bas_id))
        else:
            allros = self.get_all_ros()
        for rcli in allros:
            d = rcli.set_pool(name, ranges, next_pool)
            d.addCallback(self.onresp, 'set pool', rcli.apiaddr)
            d.addErrback(self.onerror, 'set pool', rcli.apiaddr)

    def event_rossync_del_pool(self, name, bas_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        logger.info('del pool: name={0}'.format(name))
        allros = []
        if bas_id:
            allros.append(self.get_bas_ros(bas_id))
        else:
            allros = self.get_all_ros()
        for rcli in allros:
            d = rcli.del_pool(name)
            d.addCallback(self.onresp, 'del pool', rcli.apiaddr)
            d.addErrback(self.onerror, 'del pool', rcli.apiaddr)


def __call__(dbengine = None, mcache = None, aes = None, **kwargs):
    return RouterOSPoolSyncEvent(dbengine=dbengine, mcache=mcache, aes=aes, **kwargs)