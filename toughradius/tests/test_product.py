#!/usr/bin/env python
# coding=utf-8
from toughradius.tests import TestMixin
from twisted.trial import unittest
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib.storage import Storage
from toughradius.modules.dbservice.product_service import ProductService

class ProductTestCase(unittest.TestCase, TestMixin):

    def setUp(self):
        self.init()

    def test_add_update_ppmf_product(self):
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
             'product_name': u'\u6d4b\u8bd5\u6d41\u91cf\u5305\u6708\u8d44\u8d3930G10\u5143\u81ea\u52a8\u7eed\u8d39'})
            serv = ProductService(db, self.aes)
            item = serv.add_ppmf(formdata)
            self.print_error(serv)
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata2 = Storage({'input_max_limit': '10.000',
             'bind_mac': '0',
             'flow_price': '1',
             'free_auth': '1',
             'fee_flows': '10.00',
             'product_name': u'\u6d4b\u8bd5\u6d41\u91cf\u5305\u6708\u8d44\u8d3930G10\u5143',
             'concur_number': '10',
             'free_auth_uprate': '2.000',
             'output_max_limit': '10.000',
             'bind_vlan': '0',
             'fee_price': '10.00',
             'max_giftflows': '10',
             'free_auth_downrate': '2.000',
             'product_status': '0',
             'id': pid})
            raise serv.update_ppmf(formdata2) or AssertionError
        with make_db(self.db) as db:
            raise serv.delete(pid) or AssertionError
        return

    def test_add_update_ppmonth_product(self):
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
            item = serv.add(formdata, item_charges=['TC0001'])
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata2 = Storage({'product_policy': '0',
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
             'product_status': '0',
             'product_name': '\xe9\xa2\x84\xe4\xbb\x98\xe8\xb4\xb9\xe5\x8c\x85\xe6\x9c\x8810M30\xe5\x85\x83',
             'id': pid})
            raise serv.update(formdata2, item_charges=['TC0001']) or AssertionError
        with make_db(self.db) as db:
            raise serv.delete(pid) or AssertionError
        return

    def test_add_update_pptimes_product(self):
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
            item = serv.add(formdata, item_charges=['TC0001'])
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata2 = Storage({'product_policy': '1',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_times': '0.00',
             'fee_price': '2.00',
             'fee_flows': '0.00',
             'fee_months': '0',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'output_max_limit': '10.000',
             'input_max_limit': '10.000',
             'product_name': u'\u9884\u4ed8\u8d39\u65f6\u957f\u6bcf\u5c0f\u65f62\u5143',
             'concur_number': '0',
             'product_status': '0',
             'id': pid})
            raise serv.update(formdata2, item_charges=['TC0001']) or AssertionError
        with make_db(self.db) as db:
            raise serv.delete(pid) or AssertionError
        return

    def test_add_update_bomonth_product(self):
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
            item = serv.add(formdata, item_charges=['TC0001'])
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata2 = Storage({'product_policy': '2',
             'product_name': u'\u4e70\u65ad\u5305\u5e7412\u6708300\u5143',
             'bind_mac': '0',
             'bind_vlan': '0',
             'concur_number': '0',
             'fee_months': '12',
             'fee_price': '300',
             'fee_times': '0',
             'fee_flows': '0',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'output_max_limit': '10.000',
             'input_max_limit': '10.000',
             'product_status': '0',
             'id': pid})
            raise serv.update(formdata2, item_charges=['TC0001']) or AssertionError
        with make_db(self.db) as db:
            raise serv.delete(pid) or AssertionError
        return

    def test_add_update_botimes_product(self):
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
            item = serv.add(formdata, item_charges=['TC0001'])
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata2 = Storage({'product_policy': '3',
             'product_name': u'\u4e70\u65ad\u65f6\u957f10\u5c0f\u65f65\u5143',
             'bind_mac': '0',
             'bind_vlan': '0',
             'concur_number': '0',
             'fee_months': '0',
             'fee_price': '5.00',
             'fee_times': '10.00',
             'fee_flows': '0.00',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'output_max_limit': '10.000',
             'input_max_limit': '10.000',
             'product_status': '0',
             'id': pid})
            raise serv.update(formdata2, item_charges=['TC0001']) or AssertionError
        with make_db(self.db) as db:
            raise serv.delete(pid) or AssertionError
        return

    def test_add_update_ppflows_product(self):
        pid = None
        with make_db(self.db) as db:
            formdata = Storage({'product_policy': '4',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_flows': '0',
             'fee_price': '0.5',
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
            item = serv.add(formdata, item_charges=['TC0001'])
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata2 = Storage({'product_policy': '4',
             'bind_mac': '0',
             'bind_vlan': '0',
             'fee_flows': '0',
             'fee_price': '0.5',
             'fee_months': '0',
             'fee_times': '0',
             'free_auth': '1',
             'free_auth_uprate': '1',
             'free_auth_downrate': '1',
             'concur_number': '0',
             'output_max_limit': '10',
             'input_max_limit': '10',
             'product_name': u'\u9884\u4ed8\u8d39\u6d41\u91cf0.5\u5143\u6bcfG',
             'product_status': '0',
             'id': pid})
            raise serv.update(formdata2, item_charges=['TC0001']) or AssertionError
        with make_db(self.db) as db:
            raise serv.delete(pid) or AssertionError
        return

    def test_add_update_boflows_product(self):
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
            item = serv.add(formdata, item_charges=['TC0001'])
            raise item or AssertionError
            pid = item.id
        with make_db(self.db) as db:
            formdata2 = Storage({'product_policy': '4',
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
             'product_name': u'\u4e70\u65ad\u6d41\u91cf30G5\u5143',
             'product_status': '0',
             'id': pid})
            raise serv.update(formdata2, item_charges=['TC0001']) or AssertionError
        with make_db(self.db) as db:
            raise serv.delete(pid) or AssertionError
        return