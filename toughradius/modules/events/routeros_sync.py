#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.toughlib import utils, dispatch
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib import logger
from toughradius.modules import models
from toughradius.modules.events.event_basic import BasicEvent
from toughradius.common import tools
from twisted.internet import reactor
from toughradius.modules.settings import bas_attr_cache_key
from toughradius.common.txrosapi import rospool

class RouterOSSyncEvent(BasicEvent):

    def get_bas_attr(self, bas_id, attr_name):

        def fetch_result():
            table = models.TrBasAttr.__table__
            with self.dbengine.begin() as conn:
                return conn.execute(table.select().with_only_columns([table.c.attr_value]).where(table.c.attr_name == attr_name).where(table.c.bas_id == bas_id)).scalar()

        try:
            return self.mcache.aget(bas_attr_cache_key(bas_id, attr_name), fetch_result, expire=600)
        except Exception as err:
            logger.exception(err)

    def get_bas_ros_params(self, bas_id):
        noparams = (None, None, None, None)
        api_addr = self.get_bas_attr(bas_id, 'ros_api_addr')
        if not api_addr:
            return noparams
        else:
            api_port = self.get_bas_attr(bas_id, 'ros_api_port')
            if not api_port:
                return noparams
            api_user = self.get_bas_attr(bas_id, 'ros_api_user')
            if not api_user:
                return noparams
            api_pwd = self.get_bas_attr(bas_id, 'ros_api_pwd')
            return (api_addr,
             api_port,
             api_user,
             api_pwd)

    def get_node_ross(self, node_id):
        ros_array = []
        basnode_array = []
        with make_db(self.db) as db:
            basnode_array = self.db.query(models.TrBasNode).filter(models.TrNode.id == models.TrBasNode.node_id, models.TrNode.id == node_id).all()
        for bn in basnode_array:
            try:
                api_addr, api_port, api_user, api_pwd = self.get_bas_ros_params(bn.bas_id)
                if all([api_addr, api_port, api_user]):
                    roscli = rospool.get_client(api_addr, api_port, api_user, api_pwd)
                    ros_array.append(roscli)
            except Exception as err:
                logger.error('ros connect fail： %s' % repr(err))

        return ros_array

    def get_bas_ros(self, bas_id):
        try:
            api_addr, api_port, api_user, api_pwd = self.get_bas_ros_params(bas_id)
            if all([api_addr, api_port, api_user]):
                return rospool.get_client(api_addr, api_port, api_user, api_pwd)
        except Exception as err:
            logger.error('ros connect fail： %s' % repr(err))

    def get_all_ros(self):
        ros_array = []
        bas_array = []
        with make_db(self.db) as db:
            bas_array = self.db.query(models.TrBas.id).all()
        for bas_id, in bas_array:
            api_addr, api_port, api_user, api_pwd = self.get_bas_ros_params(bas_id)
            try:
                if all([api_addr, api_port, api_user]):
                    roscli = rospool.get_client(api_addr, api_port, api_user, api_pwd)
                    ros_array.append(roscli)
            except Exception as err:
                logger.error('ros connect fail： %s' % repr(err))

        return ros_array

    def onresp(self, resp, opdesc = '', rosaddr = ''):
        logger.info('routeros<%s> sync %s result: %s' % (rosaddr, opdesc, repr(resp)), trace='routeros')

    def onerror(self, err, opdesc = '', rosaddr = ''):
        logger.error('routeros<%s> sync %s fail: %s' % (rosaddr, opdesc, repr(err)), trace='routeros')

    def event_rossync_init(self, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        self.get_all_ros()

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
    return RouterOSSyncEvent(dbengine=dbengine, mcache=mcache, aes=aes, **kwargs)