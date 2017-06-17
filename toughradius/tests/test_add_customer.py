#!/usr/bin/env python
# coding=utf-8
import datetime
from toughradius.toughlib.dbutils import make_db
from toughradius.tests import TestMixin
from twisted.trial import unittest
from toughradius.toughlib.storage import Storage
from toughradius.modules.dbservice.customer_add import CustomerAdd
from toughradius.modules.dbservice.product_service import ProductService
now = datetime.datetime.now()

class CustomerAddTestCase(unittest.TestCase, TestMixin):

    def setUp(self):
        self.init()

    def test_add_ppmf_customer(self):
        pid = None
        with make_db(self.db) as db:
            formdata = Storage({'input_max_limit': '10',
             'output_max_limit': '10',
             'bind_mac': '0',
             'flow_price': '1',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'fee_flows': '10',
             'concur_number': '0',
             'bind_vlan': '0',
             'fee_price': '10',
             'max_giftflows': '10',
             'product_name': u'\u6d4b\u8bd5\u6d41\u91cf\u5305\u6708\u8d44\u8d3930G10\u5143'})
            serv = ProductService(db, self.aes)
            item = serv.add_ppmf(formdata)
            self.print_error(serv)
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'test01',
             'password': '888888',
             'area_id': '1',
             'agency_id': None,
             'idcard': '000000',
             'builder_name': None,
             'giftflows': '1',
             'giftdays': '0',
             'charge_code': None,
             'expire_date': '3000-12-30',
             'fee_value': '120.00',
             'status': '1',
             'realname': 'test01',
             'node_id': '1',
             'account_rule': '1',
             'address': u'\u6d4b\u8bd5\u7528\u6237\u5730\u5740',
             'ip_address': None,
             'product_id': pid,
             'mobile': '000000',
             'months': '12',
             'customer_desc': u'\u6d41\u91cf\u5305\u6708\u6d4b\u8bd5\u7528\u6237'})
            serv = CustomerAdd(db, self.aes)
            ret = serv.add(formdata)
            self.print_error(serv)
            raise ret or AssertionError
        return

    def test_add_ppmonth_customer(self):
        pid = None
        with make_db(self.db) as db:
            formdata = Storage({'product_policy': '0',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_times': '0',
             'fee_flows': '0',
             'fee_price': '30',
             'fee_months': '0',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'output_max_limit': '10',
             'input_max_limit': '10',
             'concur_number': '0',
             'product_name': '\xe9\xa2\x84\xe4\xbb\x98\xe8\xb4\xb9\xe5\x8c\x85\xe6\x9c\x8810M30\xe5\x85\x83'})
            serv = ProductService(db, self.aes)
            item = serv.add(formdata)
            self.print_error(serv)
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'test02',
             'password': '888888',
             'area_id': '1',
             'idcard': '000000',
             'builder_name': None,
             'agency_id': None,
             'giftflows': '0',
             'giftdays': '0',
             'charge_code': None,
             'expire_date': '2017-06-27',
             'fee_value': '360.00',
             'status': '1',
             'realname': 'test02',
             'node_id': '1',
             'account_rule': '1',
             'address': u'\u6d4b\u8bd5\u7528\u6237\u5730\u5740',
             'ip_address': None,
             'product_id': pid,
             'mobile': '000000',
             'months': '12',
             'customer_desc': u'\u9884\u4ed8\u8d39\u5305\u6708\u6d4b\u8bd5\u7528\u6237'})
            serv = CustomerAdd(db, self.aes)
            ret = serv.add(formdata)
            self.print_error(serv)
            raise ret or AssertionError
        return

    def test_add_pptimes_customer(self):
        pid = None
        with make_db(self.db) as db:
            formdata = Storage({'product_policy': '1',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_times': '0',
             'fee_flows': '0',
             'fee_price': '2',
             'fee_months': '0',
             'free_auth': '0',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'output_max_limit': '10',
             'input_max_limit': '10',
             'concur_number': '0',
             'product_name': u'\u9884\u4ed8\u8d39\u65f6\u957f\u6bcf\u5c0f\u65f62\u5143'})
            serv = ProductService(db, self.aes)
            item = serv.add(formdata)
            self.print_error(serv)
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'test03',
             'password': '888888',
             'area_id': '1',
             'agency_id': None,
             'idcard': '000000',
             'builder_name': None,
             'giftflows': '0',
             'giftdays': '0',
             'charge_code': None,
             'expire_date': '3000-06-27',
             'fee_value': '100.00',
             'status': '1',
             'realname': 'test03',
             'node_id': '1',
             'account_rule': '1',
             'address': u'\u6d4b\u8bd5\u7528\u6237\u5730\u5740',
             'ip_address': None,
             'product_id': pid,
             'mobile': '000000',
             'months': '0',
             'customer_desc': u'\u9884\u4ed8\u8d39\u65f6\u957f\u6d4b\u8bd5\u7528\u6237'})
            serv = CustomerAdd(db, self.aes)
            ret = serv.add(formdata)
            self.print_error(serv)
            raise ret or AssertionError
        return

    def test_add_bomonth_customer(self):
        pid = None
        with make_db(self.db) as db:
            formdata = Storage({'product_policy': '2',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_flows': '0',
             'fee_price': '300',
             'fee_months': '12',
             'fee_times': '0',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'concur_number': '0',
             'output_max_limit': '10',
             'input_max_limit': '10',
             'product_name': u'\u4e70\u65ad\u5305\u5e7412\u6708300\u5143'})
            serv = ProductService(db, self.aes)
            item = serv.add(formdata)
            self.print_error(serv)
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'test04',
             'password': '888888',
             'area_id': '1',
             'idcard': '000000',
             'agency_id': None,
             'builder_name': None,
             'giftflows': '0',
             'giftdays': '0',
             'charge_code': None,
             'expire_date': '2017-06-27',
             'fee_value': '300.0',
             'status': '1',
             'realname': 'test04',
             'node_id': '1',
             'account_rule': '1',
             'address': u'\u6d4b\u8bd5\u7528\u6237\u5730\u5740',
             'ip_address': None,
             'product_id': pid,
             'mobile': '000000',
             'months': '0',
             'customer_desc': u'\u4e70\u65ad\u5305\u5e74\u6d4b\u8bd5\u7528\u6237'})
            serv = CustomerAdd(db, self.aes)
            ret = serv.add(formdata)
            self.print_error(serv)
            raise ret or AssertionError
        return

    def test_add_botimes_customer(self):
        pid = None
        with make_db(self.db) as db:
            formdata = Storage({'product_policy': '3',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_flows': '0',
             'fee_price': '5',
             'fee_months': '0',
             'fee_times': '10',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'concur_number': '0',
             'output_max_limit': '10',
             'input_max_limit': '10',
             'product_name': u'\u4e70\u65ad\u65f6\u957f10\u5c0f\u65f65\u5143'})
            serv = ProductService(db, self.aes)
            item = serv.add(formdata)
            self.print_error(serv)
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'test05',
             'password': '888888',
             'area_id': '1',
             'idcard': '000000',
             'agency_id': None,
             'builder_name': None,
             'giftflows': '0',
             'giftdays': '0',
             'charge_code': None,
             'expire_date': '3000-06-27',
             'fee_value': '5.0',
             'status': '1',
             'realname': 'test05',
             'node_id': '1',
             'account_rule': '1',
             'address': u'\u6d4b\u8bd5\u7528\u6237\u5730\u5740',
             'ip_address': None,
             'product_id': pid,
             'mobile': '000000',
             'months': '0',
             'customer_desc': u'\u4e70\u65ad\u65f6\u957f\u6d4b\u8bd5\u7528\u6237'})
            serv = CustomerAdd(db, self.aes)
            ret = serv.add(formdata)
            self.print_error(serv)
            raise ret or AssertionError
        return

    def test_add_ppflows_customer(self):
        pid = None
        with make_db(self.db) as db:
            formdata = Storage({'product_policy': '4',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_flows': '0',
             'fee_price': '0.50',
             'fee_months': '0',
             'fee_times': '0',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'concur_number': '0',
             'output_max_limit': '10',
             'input_max_limit': '10',
             'product_name': u'\u9884\u4ed8\u8d39\u6d41\u91cf0.5\u5143\u6bcfG'})
            serv = ProductService(db, self.aes)
            item = serv.add(formdata)
            self.print_error(serv)
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'test06',
             'password': '888888',
             'area_id': '1',
             'idcard': '000000',
             'agency_id': None,
             'builder_name': None,
             'giftflows': '0',
             'giftdays': '0',
             'charge_code': None,
             'expire_date': '3000-06-27',
             'fee_value': '10.0',
             'status': '1',
             'realname': 'test06',
             'node_id': '1',
             'account_rule': '1',
             'address': u'\u6d4b\u8bd5\u7528\u6237\u5730\u5740',
             'ip_address': None,
             'product_id': pid,
             'mobile': '000000',
             'months': '0',
             'customer_desc': u'\u9884\u4ed8\u8d39\u6d41\u91cf\u6d4b\u8bd5\u7528\u6237'})
            serv = CustomerAdd(db, self.aes)
            ret = serv.add(formdata)
            self.print_error(serv)
            raise ret or AssertionError
        return

    def test_add_boflows_customer(self):
        pid = None
        with make_db(self.db) as db:
            formdata = Storage({'product_policy': '5',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_flows': '30',
             'fee_price': '5',
             'fee_months': '0',
             'fee_times': '0',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'concur_number': '0',
             'output_max_limit': '10',
             'input_max_limit': '10',
             'product_name': u'\u4e70\u65ad\u6d41\u91cf30G5\u5143'})
            serv = ProductService(db, self.aes)
            item = serv.add(formdata)
            self.print_error(serv)
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata = Storage({'account_number': 'test07',
             'password': '888888',
             'area_id': '1',
             'idcard': '000000',
             'agency_id': None,
             'builder_name': None,
             'giftflows': '0',
             'giftdays': '0',
             'charge_code': None,
             'expire_date': '3000-06-27',
             'fee_value': '5.0',
             'status': '1',
             'realname': 'test07',
             'node_id': '1',
             'account_rule': '1',
             'address': u'\u6d4b\u8bd5\u7528\u6237\u5730\u5740',
             'ip_address': None,
             'product_id': pid,
             'mobile': '000000',
             'months': '0',
             'customer_desc': u'\u4e70\u65ad\u6d41\u91cf\u6d4b\u8bd5\u7528\u6237'})
            serv = CustomerAdd(db, self.aes)
            ret = serv.add(formdata)
            self.print_error(serv)
            raise ret or AssertionError
        return