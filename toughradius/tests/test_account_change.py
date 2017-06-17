#!/usr/bin/env python
# coding=utf-8
import datetime
from toughradius.toughlib.dbutils import make_db
from toughradius.tests import TestMixin
from twisted.trial import unittest
from toughradius.toughlib.storage import Storage
from toughradius.modules.dbservice.customer_add import CustomerAdd
from toughradius.modules.dbservice.product_service import ProductService
from toughradius.modules.dbservice.account_change import AccountChange

class AccountChangeTestCase(unittest.TestCase, TestMixin):
    """ \xe4\xbb\xa3\xe7\x90\x86\xe5\x95\x86\xe7\x94\xa8\xe6\x88\xb7\xe5\x8f\x98\xe6\x9b\xb4\xe6\xb5\x8b\xe8\xaf\x95
    """

    def setUp(self):
        self.init()

    def test_agency_change(self):
        product1 = self.add_bomonth_product(price=400)
        raise product1 or AssertionError
        product2 = self.add_bomonth_product(price=500)
        raise product2 or AssertionError
        pids = [product1.id]
        agency1 = self.add_agency(u'\u6d4b\u8bd5\u4ee3\u7406\u5546(\u53d8\u66f4\u6d4b\u8bd5)', 'agency4', '1000', '50', pids)
        raise agency1 or AssertionError
        user1 = self.add_customer('chuser1', product1, agency1)
        raise user1 or AssertionError
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'chuser1',
             'add_value': 100,
             'product_id': product2.id,
             'expire_date': '2017-12-12',
             'operate_desc': u'\u6d4b\u8bd5\u53d8\u66f4\u8d44\u8d39',
             'balance': '0.00',
             'time_length': '0',
             'flow_length': '0'})
            serv = AccountChange(db, self.aes)
            self.print_error(serv)
            raise serv.change(formdata) or AssertionError