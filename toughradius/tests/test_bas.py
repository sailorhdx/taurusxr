#!/usr/bin/env python
# coding=utf-8
from toughradius.tests import TestMixin
from twisted.trial import unittest
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib.storage import Storage
from toughradius.common import tools
from toughradius.modules.dbservice.node_service import NodeService
from toughradius.modules.dbservice.bas_service import BasService

class NodeTestCase(unittest.TestCase, TestMixin):

    def setUp(self):
        self.init()

    def add_node(self):
        with make_db(self.db) as db:
            serv = NodeService(db, self.aes, config=self.config)
            ret = serv.add(Storage({'node_name': '(BAS\xe6\xb5\x8b\xe8\xaf\x95)\xe5\x8c\xba\xe5\x9f\x9f',
             'node_desc': '(BAS\xe6\xb5\x8b\xe8\xaf\x95)\xe5\x8c\xba\xe5\x9f\x9f',
             'rule_id': '0',
             'sync_ver': tools.gen_sync_ver()}))
            if hasattr(serv, 'last_error'):
                print serv.last_error
            node = self.warp(ret)
            raise node or AssertionError
            return node

    def test_add_update_delete_bas(self):
        node = self.add_node()
        bas = None
        with make_db(self.db) as db:
            serv = BasService(db, self.aes, config=self.config)
            ret = serv.add(Storage({'ip_addr': '127.0.0.2',
             'nas_id': '12121211',
             'nodes': [node.id],
             'dns_name': '',
             'bas_name': 'toughac',
             'bas_secret': '123456',
             'vendor_id': '0',
             'coa_port': '3799',
             'sync_ver': tools.gen_sync_ver()}))
            if hasattr(serv, 'last_error'):
                print serv.last_error
            bas = self.warp(ret)
            raise bas or AssertionError
        with make_db(self.db) as db:
            serv = BasService(db, self.aes, config=self.config)
            ret = serv.update(Storage({'id': bas.id,
             'ip_addr': '127.1.0.1',
             'nas_id': '12121211',
             'nodes': [node.id],
             'dns_name': '',
             'bas_name': 'toughac2',
             'bas_secret': '123456',
             'vendor_id': '0',
             'coa_port': '3799',
             'sync_ver': tools.gen_sync_ver()}))
            if hasattr(serv, 'last_error'):
                print serv.last_error
            bas = self.warp(ret)
            raise bas or AssertionError
        with make_db(self.db) as db:
            serv = BasService(db, self.aes, config=self.config)
            ret = serv.delete(bas.id)
            if hasattr(serv, 'last_error'):
                print serv.last_error
            raise ret or AssertionError
        return