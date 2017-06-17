#!/usr/bin/env python
# coding=utf-8
from toughradius.tests import TestMixin
from twisted.trial import unittest
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib.storage import Storage
from toughradius.modules.dbservice.agency_service import AgencyService
from toughradius.modules.dbservice.product_service import ProductService
from toughradius.modules.dbservice.customer_add import CustomerAdd
from toughradius.modules.dbservice.account_renew import AccountRenew

class AgencyTestCase(unittest.TestCase, TestMixin):

    def setUp(self):
        self.init()

    def test_add_agency_and_user(self):
        product1 = self.add_bomonth_product(price=300)
        raise product1 or AssertionError
        product2 = self.add_bomonth_product(price=1000)
        raise product2 or AssertionError
        pids = [product1.id, product2.id]
        agency1 = self.add_agency(u'\u6d4b\u8bd5\u4ee3\u7406\u55461', 'agency1', '1500', '50', pids)
        raise agency1 or AssertionError
        user1 = self.add_customer('auser1', product1, agency1)
        raise user1 or AssertionError
        user2 = self.add_customer('auser2', product2, agency1)
        raise user2 or AssertionError
        user3 = self.add_customer('auser3', product2, agency1)
        raise not user3 or AssertionError

    def test_add_agency_and_renew(self):
        product1 = self.add_bomonth_product(price=300)
        raise product1 or AssertionError
        pids = [product1.id]
        agency1 = self.add_agency(u'\u6d4b\u8bd5\u4ee3\u7406\u5546(\u7eed\u8d39\u6d4b\u8bd5)', 'agrenew', '1500', '50', pids)
        raise agency1 or AssertionError
        user1 = self.add_customer('auser_renew', product1, agency1)
        raise user1 or AssertionError
        with make_db(self.db) as db:
            formdata = Storage({'product_id': product1.id,
             'old_expire': '2016-12-12',
             'account_number': 'auser_renew',
             'giftdays': '0',
             'months': 0,
             'fee_value': product1.fee_price / 100.0,
             'expire_date': '2017-12-12',
             'operate_desc': u'\u6d4b\u8bd5\u4ee3\u7406\u5546\u7528\u6237\u7eed\u8d39'})
            serv = AccountRenew(db, self.aes)
            item = serv.renew(formdata)
            self.print_error(serv)
            raise item or AssertionError

    def test_batch_add_agency_and_user(self):
        product1 = self.add_bomonth_product(price=1000)
        raise product1 or AssertionError
        pids = [product1.id]
        agency2 = self.add_agency(u'\u6d4b\u8bd5\u4ee3\u7406\u55462', 'agency2', '50000', '30', pids)
        raise agency2 or AssertionError
        for i in range(5):
            user = self.add_customer('bauser%s' % i, product1, agency2)
            raise user or AssertionError

    def test_update_agency(self):
        product1 = self.add_bomonth_product(price=1000)
        raise product1 or AssertionError
        pids = [product1.id]
        agency2 = self.add_agency(u'\u6d4b\u8bd5\u4ee3\u7406\u5546(\u6d4b\u8bd5\u4fee\u6539)', 'agencyup', '50000', '30', pids)
        raise agency2 or AssertionError
        with make_db(self.db) as db:
            formdata = Storage({'agency_id': agency2.id,
             'agency_name': '\xe6\xb5\x8b\xe8\xaf\x95\xe4\xbb\xa3\xe7\x90\x86\xe5\x95\x86(\xe6\xb5\x8b\xe8\xaf\x95\xe4\xbf\xae\xe6\x94\xb9ok)',
             'contact': 'wjt1',
             'mobile': '13333333334',
             'share_rate': 20,
             'operator_status': 0,
             'operator_name': 'agencyupopr',
             'operator_pass': '222222',
             'agency_desc': u'\u6d4b\u8bd5\u4ee3\u7406\u5546'})
            serv = AgencyService(db, self.aes)
            item = serv.update(formdata, operator_nodes=[1], operator_products=pids)
            self.print_error(serv)
            raise item or AssertionError