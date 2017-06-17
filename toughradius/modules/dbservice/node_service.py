#!/usr/bin/env python
# coding=utf-8
import datetime
from toughradius.modules.settings import *
from hashlib import md5
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.common import tools
from toughradius.toughlib import utils, dispatch, logger
from toughradius.toughlib.storage import Storage
from toughradius.modules.dbservice import BaseService
from toughradius.modules.dbservice import logparams
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD

class NodeService(BaseService):

    def get_safe_node(self, node_id):
        node = self.db.query(models.TrNode).get(node_id)
        if not node:
            raise ValueError(u'区域节点不存在')
        return node

    @logparams
    def add(self, formdata, bas_ids = [], **kwargs):
        try:
            node = models.TrNode()
            node.id = formdata.node_id if 'node_id' in formdata else utils.get_uuid()
            node.node_name = formdata.node_name
            node.node_type = utils.safeunicode(formdata.get('node_type', 'other'))
            node.rule_id = formdata.rule_id
            node.node_desc = formdata.get('node_desc', '')
            node.sync_ver = tools.gen_sync_ver()
            self.db.add(node)
            for bas_id in bas_ids:
                basnode = models.TrBasNode()
                basnode.bas_id = bas_id
                basnode.node_id = node.id
                basnode.sync_ver = tools.gen_sync_ver()
                self.db.add(basnode)
            self.add_oplog(u'新增区域信息:%s' % utils.safeunicode(formdata.node_name))
            self.db.commit()
            return node
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='node_add_error')
            self.last_error = u'区域创建失败:%s' % utils.safeunicode(err)
            return False

    @logparams
    def update(self, formdata, bas_ids = [], **kwargs):
        try:
            node = self.get_safe_node(formdata.id)
            node.node_type = utils.safeunicode(formdata.get('node_type', 'other'))
            node.node_name = formdata.node_name
            node.node_desc = formdata.get('node_desc', '')
            if 'rule_id' in formdata:
                node.rule_id = formdata.rule_id
            node.sync_ver = tools.gen_sync_ver()
            self.db.query(models.TrBasNode).filter_by(node_id=node.id).delete()
            for bas_id in bas_ids:
                basnode = models.TrBasNode()
                basnode.bas_id = bas_id
                basnode.node_id = node.id
                basnode.sync_ver = tools.gen_sync_ver()
                self.db.add(basnode)
            self.add_oplog(u'修改区域信息:%s' % utils.safeunicode(formdata.node_name))
            self.db.commit()
            return node
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='node_update_error')
            self.last_error = u'修改区域失败:%s' % utils.safeunicode(err)
            return False

    @logparams
    def delete(self, node_id, **kwargs):
        try:
            node = self.get_safe_node(node_id)
            if self.db.query(models.TrCustomer.customer_id).filter_by(node_id=node_id).count() > 0:
                raise ValueError(u'该区域节点下有用户，不允许删除')
            self.db.query(models.TrNode).filter_by(id=node_id).delete()
            abuuilders = []
            for area in self.db.query(models.TrArea).filter_by(node_id=node_id):
                abuuilders.append(area_id=area.id)
                self.db.query(models.TrAreaBuilder).filter_by(area_id=area.id).delete()

            self.db.query(models.TrNodeAttr).filter_by(node_id=node_id).delete()
            self.db.query(models.TrArea).filter_by(node_id=node_id).delete()
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrNode.__tablename__, dict(id=node_id)), async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrArea.__tablename__, dict(node_id=node_id)), async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrNodeAttr.__tablename__, dict(node_id=node_id)), async=True)
            for abid in abuuilders:
                dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAreaBuilder.__tablename__, dict(area_id=abid)), async=True)

            self.add_oplog(u'删除区域信息:%s' % node_id)
            self.db.commit()
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='node_delete_error')
            self.last_error = u'删除区域失败:%s' % utils.safeunicode(err)
            return False