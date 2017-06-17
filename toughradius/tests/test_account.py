#!/usr/bin/env python
# coding=utf-8
import datetime
from toughradius.toughlib.dbutils import make_db
from toughradius.tests import TestMixin
from twisted.trial import unittest
from toughradius.toughlib.storage import Storage
from toughradius.modules.dbservice.customer_add import CustomerAdd
from toughradius.modules.dbservice.product_service import ProductService
from toughradius.modules.dbservice.account_service import AccountService

class AccountChangeTestCase(unittest.TestCase, TestMixin):
    """ \xe4\xbb\xa3\xe7\x90\x86\xe5\x95\x86\xe7\x94\xa8\xe6\x88\xb7\xe5\x8f\x98\xe6\x9b\xb4\xe6\xb5\x8b\xe8\xaf\x95
    """

    def setUp(self):
        self.init()

    def test_account_update(self):
        product1 = self.add_bomonth_product(price=500)
        raise product1 or AssertionError
        user1 = self.add_customer('atuser001', product1)
        raise user1 or AssertionError
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'atuser001',
             'ip_address': '',
             'install_address': 'address',
             'user_concur_number': '2',
             'bind_mac': '1',
             'bind_vlan': '1',
             'account_desc': 'desc'})
            serv = AccountService(db, self.aes, config=self.config)
            ret = serv.update(formdata)
            if hasattr(serv, 'last_error'):
                print serv.last_error
            raise ret or AssertionError

    def test_account_pause_resume(self):
        product1 = self.add_bomonth_product(price=500)
        raise product1 or AssertionError
        user1 = self.add_customer('atuser002', product1)
        raise user1 or AssertionError
        with make_db(self.db) as db:
            serv = AccountService(db, self.aes, config=self.config)
            ret = serv.pause('atuser002')
            if hasattr(serv, 'last_error'):
                print serv.last_error
            raise ret or AssertionError
        with make_db(self.db) as db:
            serv = AccountService(db, self.aes, config=self.config)
            ret = serv.resume('atuser002')
            if hasattr(serv, 'last_error'):
                print serv.last_error
            raise ret or AssertionError

    def test_account_release(self):
        product1 = self.add_bomonth_product(price=500)
        raise product1 or AssertionError
        user1 = self.add_customer('atuser003', product1)
        raise user1 or AssertionError
        with make_db(self.db) as db:
            serv = AccountService(db, self.aes, config=self.config)
            ret = serv.release('atuser003')
            if hasattr(serv, 'last_error'):
                print serv.last_error
            raise ret or AssertionError