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
            logger.error('bas sync not support', trace='routeros')
        except Exception as err:
            logger.error('ros connect fail： %s' % repr(err), trace='routeros')

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
                logger.error('ros connect fail： %s' % repr(err), trace='routeros')

        return ros_array

    def get_product_profile(self, pid):
        product = self.db.query(models.TrProduct).get(pid)
        pool = self.db.query(models.TrProductAttr.attr_value).filter_by(product_id=pid, attr_name='Framed-Pool').scalar()
        rate_limit = '%sk/%sk' % (product.input_max_limit / 1024, product.output_max_limit / 1024)
        return (product.id, pool, rate_limit)

    def onresp(self, resp, opdesc = '', rosaddr = ''):
        logger.info('routeros<%s> sync %s result: %s' % (rosaddr, opdesc, repr(resp)), trace='routeros')

    def onerror(self, err, opdesc = '', rosaddr = ''):
        logger.error('routeros<%s> sync %s fail: %s' % (rosaddr, opdesc, repr(err)), trace='routeros')

    def event_rossync_init(self, **kwargs):
        """ routeros api client init
        """
        if os.environ.get('LICENSE_TYPE', '') not in ('taurusxee', 'routeros-oem'):
            return
        self.get_all_ros()

    def event_rossync_reload(self, bas_id):
        apiaddr, apiport, apiuser, apipwd = self.get_bas_ros_params(bas_id)
        rospool.reload_client(apiaddr, apiport, apiuser, apipwd)