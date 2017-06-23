#!/usr/bin/env python
# coding=utf-8
from twisted.trial import unittest
from taurusxradius.taurusxlib.dbutils import make_db
from taurusxradius.taurusxlib.dbengine import get_engine
from taurusxradius.taurusxlib import config as iconfig
from taurusxradius.taurusxlib.storage import Storage
from sqlalchemy.orm import scoped_session, sessionmaker
from taurusxradius.taurusxlib.config import redis_conf
from taurusxradius.taurusxlib.redis_cache import CacheManager
from taurusxradius.taurusxlib import utils, logger
import os

class TestMixin(object):

    def init(self):
        _dir = os.path.dirname(__file__)
        self.config = iconfig.find_config(os.path.join(_dir, 'test.json'))
        logger.Logger(self.config, 'taurusxee-test')
        self.dbengine = get_engine(self.config)
        self.db = scoped_session(sessionmaker(bind=self.dbengine, autocommit=False, autoflush=True))
        self.aes = utils.AESCipher(key=self.config.system.secret)

    def warp(self, mdl):
        if not hasattr(mdl, '__table__'):
            return
        data = Storage()
        for c in mdl.__table__.columns:
            data[c.name] = getattr(mdl, c.name)

        return data

    def print_error(self, serv):
        if hasattr(serv, 'last_error'):
            print serv.last_error

    def add_bomonth_product(self, price = 0, fee_months = 12):
        from taurusxradius.modules.dbservice.product_service import ProductService
        with make_db(self.db) as db:
            formdata = Storage({'product_policy': '2',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_flows': '0',
             'fee_price': str(price),
             'fee_months': str(fee_months),
             'fee_times': '0',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'concur_number': '0',
             'output_max_limit': '10',
             'input_max_limit': '10',
             'product_name': u'\u4e70\u65ad\u5305\u5e74%s\u6708%s\u5143' % (fee_months, price)})
            serv = ProductService(db, self.aes)
            item = serv.add(formdata, item_charges=[])
            self.print_error(serv)
            return self.warp(item)

    def add_agency(self, name, opr, amount, rate, pids = []):
        from taurusxradius.modules.dbservice.agency_service import AgencyService
        with make_db(self.db) as db:
            formdata = Storage({'agency_name': name,
             'contact': 'wjt',
             'mobile': '13333333333',
             'amount': amount,
             'share_rate': rate,
             'operator_name': opr,
             'operator_pass': '111111',
             'agency_desc': u'\u6d4b\u8bd5\u4ee3\u7406\u5546'})
            serv = AgencyService(db, self.aes)
            item = serv.add(formdata, operator_nodes=[1], operator_products=pids)
            self.print_error(serv)
            return self.warp(item)

    def add_customer(self, username, product, agency = None):
        from taurusxradius.modules.dbservice.customer_add import CustomerAdd
        with make_db(self.db) as db:
            formdata = Storage({'account_number': username,
             'password': '888888',
             'area_id': '1',
             'idcard': '000000',
             'agency_id': str(agency.id) if agency else None,
             'builder_name': None,
             'giftflows': '0',
             'giftdays': '0',
             'charge_code': None,
             'expire_date': '2017-06-27',
             'fee_value': str(product.fee_price / 100.0),
             'status': '1',
             'realname': 'r_%s' % username,
             'node_id': '1',
             'account_rule': '1',
             'address': u'\u6d4b\u8bd5\u7528\u6237\u5730\u5740',
             'ip_address': None,
             'product_id': str(product.id),
             'mobile': '000000',
             'months': '0',
             'customer_desc': u'\u6d4b\u8bd5\u7528\u6237'})
            serv = CustomerAdd(db, self.aes)
            cuser = serv.add(formdata)
            self.print_error(serv)
            return cuser
        return