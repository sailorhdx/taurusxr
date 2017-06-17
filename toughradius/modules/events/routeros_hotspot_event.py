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

class RouterOSHotspotSyncEvent(RouterOSSyncEvent):

    def event_rossync_resync_hotspot_profile(self, bas_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        try:
            logger.info('resync hotspot profile: bas_id={0}'.format(bas_id))
            rcli = self.get_bas_ros(bas_id)

            def update_profile(resp, name, pool, rate_limit):
                d = rcli.add_hotspot_profile(name, pool, rate_limit)
                d.addCallback(self.onresp, 'add hotspot profile', rcli.apiaddr)
                d.addErrback(self.onerror, 'add hotspot profile', rcli.apiaddr)

            with make_db(self.db) as db:
                for pid, in self.db.query(models.TrProduct.id).all():
                    name, pool, rate_limit = self.get_product_profile(pid)
                    dg = rcli.del_hotspot_profile(name)
                    dg.addCallback(update_profile, name, pool, rate_limit)
                    dg.addErrback(self.onerror, 'del hotspot profile', rcli.apiaddr)

        except Exception as err:
            logger.exception(err)

    def event_rossync_set_hotspot_profile(self, name, pool = None, rate_limit = None, bas_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        logger.info('set hotspot profile: name={0}, {1} {2}'.format(name, pool, rate_limit))
        allros = []
        if bas_id:
            allros.append(self.get_bas_ros(bas_id))
        else:
            allros = self.get_all_ros()

        def update_profile(resp, rcli):
            d = rcli.add_hotspot_profile(name, pool, rate_limit)
            d.addCallback(self.onresp, 'add hotspot profile', rcli.apiaddr)
            d.addErrback(self.onerror, 'add hotspot profile', rcli.apiaddr)

        for rcli in allros:
            d = rcli.del_hotspot_profile(name)
            d.addCallback(update_profile, rcli)
            d.addErrback(self.onerror, 'set hotspot profile', rcli.apiaddr)

    def event_rossync_del_hotspot_profile(self, name, bas_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        logger.info('del hotspot profile: name={0}'.format(name))
        allros = []
        if bas_id:
            allros.append(self.get_bas_ros(bas_id))
        else:
            allros = self.get_all_ros()
        for rcli in allros:
            d = rcli.del_hotspot_profile(name)
            d.addCallback(self.onresp, 'del hotspot profile', rcli.apiaddr)
            d.addErrback(self.onerror, 'del hotspot profile', rcli.apiaddr)

    def event_rossync_resync_hotspot_user(self, bas_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        try:
            logger.info('resync hotspot user: bas_id={0}'.format(bas_id))
            rcli = self.get_bas_ros(bas_id)

            def update_user(resp, name, password, profile):
                d = rcli.add_hotspot_user(name, password, profile)
                d.addCallback(self.onresp, 'add hotspot user', rcli.apiaddr)
                d.addErrback(self.onerror, 'add hotspot user', rcli.apiaddr)

            with make_db(self.db) as db:
                for node_id, in db.query(models.TrNode.id).filter(models.TrBasNode.node_id == models.TrNode.id, models.TrNode.node_type == 'hotspot', models.TrBasNode.bas_id == bas_id):
                    for user in self.db.query(models.TrAccount).filter(models.TrAccount.status < 2, models.TrAccount.expire_date >= utils.get_currdate(), models.TrAccount.customer_id == models.TrCustomer.customer_id, models.TrCustomer.node_id == node_id):
                        dg = rcli.del_hotspot_user(user.account_number)
                        dg.addCallback(update_user, user.account_number, self.aes.decrypt(user.password), user.product_id)
                        dg.addErrback(self.onerror, 'del hotspot user', rcli.apiaddr)

        except Exception as err:
            logger.exception(err)

    def event_rossync_set_hotspot_user(self, name, password = None, profile = None, node_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        with make_db(self.db) as db:
            if node_id and db.query(models.TrNode.id).filter_by(id=node_id, node_type='hotspot').count() == 0:
                logger.info('%s not hotspot user' % name)
                return
        logger.info('set hotspot user: name={0}, {1} {2}'.format(name, '******', profile))
        allros = []
        if node_id:
            allros = self.get_node_ross(node_id)
        else:
            allros = self.get_all_ros()

        def update_user(resp, rcli, name, password, profile):
            ud = rcli.add_hotspot_user(name, password, profile)
            ud.addCallback(self.onresp, 'add hotspot user', rcli.apiaddr)
            ud.addErrback(self.onerror, 'add hotspot user', rcli.apiaddr)

        for rcli in allros:
            d = rcli.del_hotspot_user(name)
            d.addCallback(update_user, rcli, name, password, profile)
            d.addErrback(self.onerror, 'del hotspot user', rcli.apiaddr)

    def event_rossync_del_hotspot_user(self, name, node_id = None, **kwargs):
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        logger.info('del hotspot user: name={0}'.format(name))
        allros = []
        if node_id:
            allros = self.get_node_ross(node_id)
        else:
            allros = self.get_all_ros()
        for rcli in allros:
            d = rcli.del_hotspot_user(name)
            d.addCallback(self.onresp, 'del hotspot user', rcli.apiaddr)
            d.addErrback(self.onerror, 'del hotspot user', rcli.apiaddr)


def __call__(dbengine = None, mcache = None, aes = None, **kwargs):
    return RouterOSHotspotSyncEvent(dbengine=dbengine, mcache=mcache, aes=aes, **kwargs)