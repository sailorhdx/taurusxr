#!/usr/bin/env python
# coding=utf-8
import sys
import time
import os
from twisted.python import log
from twisted.internet import task
from twisted.internet import protocol
from twisted.internet import reactor
from toughradius.txportal.packet import cmcc, huawei
from toughradius.toughlib import utils, logger
from toughradius.toughlib import redis_cache
from toughradius.modules import models
from toughradius.modules import settings
from toughradius.toughlib.config import redis_conf

class PortalListen(protocol.DatagramProtocol):

    def __init__(self, config, dbengine = None, **kwargs):
        self.dbengine = dbengine
        self.config = config
        self.mcache = redis_cache.CacheManager(redis_conf(config), cache_name='Portald')
        self.actions = {huawei.NTF_LOGOUT: self.doAckNtfLogout}
        reactor.callLater(3.0, self.init_task)

    def get_nas(self, ip_addr):

        def fetch_result():
            table = models.TrwBas.__table__
            with self.db_engine.begin() as conn:
                return conn.execute(table.select().where(table.c.ip_addr == ip_addr)).first()

        return self.mcache.aget(settings.wlanportal_cache_key(ip_addr), fetch_result, expire=600)

    def init_task(self):
        _task = task.LoopingCall(self.send_ntf_heart)
        _task.start(self.config.portal.ntf_heart)

    def send_ntf_heart(self):
        pass

    def doAckNtfLogout(self, req, vendor, secret, (host, port)):
        try:
            resp = vendor.proto.newMessage(vendor.ACK_NTF_LOGOUT, req.userIp, req.serialNo, req.reqId, str(secret))
            logger.info('Send portal packet to %s:%s: %s' % (host, port, utils.safestr(req)))
            self.transport.write(str(resp), (host, port))
        except Exception as err:
            logger.exception(err)

    def datagramReceived(self, datagram, (host, port)):
        try:
            nas = self.get_nas(host)
            ac_addr = nas['ip_addr']
            ac_port = int(nas['ac_port'])
            secret = utils.safestr(nas['bas_secret'])
            _vendor = utils.safestr(nas['portal_vendor'])
            if _vendor not in ('cmccv1', 'cmccv2', 'huaweiv1', 'huaweiv2'):
                self.render_error(msg=u'AC server portal_vendor {0} not support '.format(_vendor))
                return
            vendor = client.PortalClient.vendors.get(_vendor)
            req = vendor.proto(secret=secret, packet=datagram, source=(host, port))
            logger.info('Received portal packet from %s:%s: %s' % (host, port, utils.safestr(req)))
            if req.type in self.actions:
                self.actions[req.type](req, vendor, secret, (host, port))
            else:
                logger.error('Not support packet from ac host ' + host)
        except Exception as err:
            logger.error('Dropping invalid packet from %s: %s' % ((host, port), utils.safestr(err)))


def run(config, dbengine = None, log = None):
    app = PortalListen(config, dbengine=dbengine, log=log)
    reactor.listenUDP(int(config.portal.listen), app, interface=config.portal.host)