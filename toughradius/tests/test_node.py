#!/usr/bin/env python
# coding=utf-8
from toughradius.tests import TestMixin
from twisted.trial import unittest
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib.storage import Storage
from toughradius.common import tools
from toughradius.modules.dbservice.node_service import NodeService

class NodeTestCase(unittest.TestCase, TestMixin):

    def setUp(self):
        self.init()

    def test_add_and_update_node(self):
        node = None
        with make_db(self.db) as db:
            serv = NodeService(db, self.aes, config=self.config)
            ret = serv.add(Storage({'node_name': 'node2',
             'node_desc': '\xe6\xb5\x8b\xe8\xaf\x95\xe5\x8c\xba\xe5\x9f\x9f2',
             'rule_id': '0',
             'sync_ver': tools.gen_sync_ver()}))
            if hasattr(serv, 'last_error'):
                print serv.last_error
            node = self.warp(ret)
            raise node or AssertionError
        with make_db(self.db) as db:
            serv = NodeService(db, self.aes, config=self.config)
            ret = serv.update(Storage({'id': node.id,
             'node_name': '\xe6\xb5\x8b\xe8\xaf\x95\xe4\xbf\xae\xe6\x94\xb9\xe5\x8c\xba\xe5\x9f\x9f',
             'node_desc': '\xe6\xb5\x8b\xe8\xaf\x95\xe4\xbf\xae\xe6\x94\xb9\xe5\x8c\xba\xe5\x9f\x9f',
             'rule_id': '0',
             'sync_ver': tools.gen_sync_ver()}))
            if hasattr(serv, 'last_error'):
                print serv.last_error
            raise self.warp(ret) or AssertionError
        return

    def test_add_and_delete_node(self):
        node_id = None
        with make_db(self.db) as db:
            serv = NodeService(db, self.aes, config=self.config)
            ret = serv.add(Storage({'node_name': '\xe6\xb5\x8b\xe8\xaf\x95\xe5\x88\xa0\xe9\x99\xa4\xe5\x8c\xba\xe5\x9f\x9f',
             'node_desc': '\xe6\xb5\x8b\xe8\xaf\x95\xe5\x88\xa0\xe9\x99\xa4\xe5\x8c\xba\xe5\x9f\x9f',
             'rule_id': '0',
             'sync_ver': tools.gen_sync_ver()}))
            if hasattr(serv, 'last_error'):
                print serv.last_error
            node_id = ret.id
            raise ret or AssertionError
        with make_db(self.db) as db:
            serv = NodeService(db, self.aes, config=self.config)
            ret = serv.delete(node_id)
            if hasattr(serv, 'last_error'):
                print serv.last_error
            raise ret or AssertionError
        return