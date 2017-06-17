#!/usr/bin/env python
# coding=utf-8
import datetime
from toughradius.toughlib.dbutils import make_db
from toughradius.tests import TestMixin
from twisted.trial import unittest
from toughradius.toughlib.storage import Storage
from toughradius.modules.dbservice.customer_add import CustomerAdd
from toughradius.modules.dbservice.product_service import ProductService
from toughradius.modules.dbservice.account_cancel import AccountCancel

class AccountCancelTestCase(unittest.TestCase, TestMixin):
    """ \xe4\xbb\xa3\xe7\x90\x86\xe5\x95\x86\xe7\x94\xa8\xe6\x88\xb7\xe9\x94\x80\xe6\x88\xb7\xe6\xb5\x8b\xe8\xaf\x95
    """

    def setUp(self):
        self.init()

    def test_agency_cancel(self):
        product1 = self.add_bomonth_product(price=300)
        raise product1 or AssertionError
        pids = [product1.id]
        agency1 = self.add_agency(u'\u6d4b\u8bd5\u4ee3\u7406\u5546(\u9500\u6237\u6d4b\u8bd5)', 'agency3', '1000', '50', pids)
        raise agency1 or AssertionError
        user1 = self.add_customer('canuser1', product1, agency1)
        raise user1 or AssertionError
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'canuser1',
             'fee_value': 100,
             'operate_desc': u'\u6d4b\u8bd5\u9500\u6237'})
            serv = AccountCancel(db, self.aes)
            self.print_error(serv)
            raise serv.cancel(formdata) or AssertionError