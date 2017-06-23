#!/usr/bin/env python
# coding=utf-8
import sys, struct
from taurusxradius.taurusxlib import utils, httpclient
from taurusxradius.taurusxlib import dispatch, logger
from taurusxradius.modules import models
from taurusxradius.taurusxlib.dbutils import make_db
from taurusxradius.modules.tasks.task_base import TaseBasic
from twisted.internet import reactor, defer
from twisted.names import client, dns
from taurusxradius.modules import taskd

class DdnsUpdateTask(TaseBasic):
    __name__ = 'ddns-update'

    def get_next_interval(self):
        return 60

    def first_delay(self):
        return 5

    @defer.inlineCallbacks
    def process(self, *args, **kwargs):
        self.logtimes()
        with make_db(self.db) as db:
            try:
                nas_list = db.query(models.TrBas)
                for nas in nas_list:
                    if not nas.dns_name:
                        continue
                    results, _, _ = yield client.lookupAddress(nas.dns_name)
                    if not results:
                        logger.info('domain {0} resolver empty'.format(nas.dns_name))
                    if results[0].type == dns.A:
                        ipaddr = '.'.join((str(i) for i in struct.unpack('BBBB', results[0].payload.address)))
                        if ipaddr:
                            nas.ip_addr = ipaddr
                            db.commit()
                            logger.info('domain {0} resolver {1}  success'.format(nas.dns_name, ipaddr))
                    else:
                        logger.info('domain {0} no ip address,{1}'.format(nas.dns_name, repr(results)))

            except Exception as err:
                logger.error('ddns process error %s' % utils.safeunicode(err.message))

        defer.returnValue(60)


taskd.TaskDaemon.__taskclss__.append(DdnsUpdateTask)