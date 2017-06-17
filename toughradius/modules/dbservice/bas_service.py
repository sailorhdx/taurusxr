#!/usr/bin/env python
# coding=utf-8
import json
import datetime
from toughradius.modules.settings import *
from hashlib import md5
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.toughlib import utils, dispatch, logger
from toughradius.toughlib.storage import Storage
from toughradius.common import tools
from toughradius.modules.dbservice import BaseService
from toughradius.modules.dbservice import logparams
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.modules.events.settings import CACHE_DELETE_EVENT

class BasService(BaseService):

    @logparams
    def add(self, formdata, nodes = [], **kwargs):
        try:
            if not formdata.ip_addr:
                raise ValueError(u'接入设备地址不能为空')
            if self.db.query(models.TrBas.id).filter_by(ip_addr=formdata.ip_addr).count() > 0:
                raise ValueError(u'接入设备地址已经存在')
            if self.db.query(models.TrBas.id).filter_by(nas_id=formdata.nas_id).count() > 0:
                raise ValueError(u'接入设备标识已经存在')
            bas = models.TrBas()
            bas.id = utils.get_uuid()
            bas.nas_id = formdata.get('nas_id', '')
            bas.ip_addr = formdata.ip_addr
            bas.dns_name = formdata.get('dns_name', '')
            bas.bas_name = formdata.bas_name
            bas.vendor_id = formdata.vendor_id
            bas.bas_secret = formdata.bas_secret
            bas.coa_port = formdata.coa_port
            bas.portal_vendor = formdata.portal_vendor
            bas.ac_port = formdata.ac_port
            bas.time_type = formdata.get('time_type', 0)
            bas.sync_ver = tools.gen_sync_ver()
            self.db.add(bas)
            for node_id in nodes:
                basnode = models.TrBasNode()
                basnode.bas_id = bas.id
                basnode.node_id = node_id
                basnode.sync_ver = tools.gen_sync_ver()
                self.db.add(basnode)

            self.add_oplog(u'新增接入设备信息:%s' % bas.ip_addr)
            self.db.commit()
            return bas
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='bas_add_error')
            self.last_error = u'接入设备创建失败:%s' % utils.safeunicode(err)
            return False

    @logparams
    def update(self, formdata, nodes = [], **kwargs):
        try:
            bas = self.db.query(models.TrBas).get(formdata.id)
            bas.ip_addr = formdata.ip_addr
            if 'nas_id' in formdata:
                bas.nas_id = formdata.nas_id
            if 'dns_name' in formdata:
                bas.dns_name = formdata.dns_name
            if 'bas_name' in formdata:
                bas.bas_name = formdata.bas_name
            if 'vendor_id' in formdata:
                bas.vendor_id = formdata.vendor_id
            if 'bas_secret' in formdata:
                bas.bas_secret = formdata.bas_secret
            if 'coa_port' in formdata:
                bas.coa_port = formdata.coa_port
            if 'portal_vendor' in formdata:
                bas.portal_vendor = formdata.portal_vendor
            if 'ac_port' in formdata:
                bas.ac_port = formdata.ac_port
            bas.sync_ver = tools.gen_sync_ver()
            self.db.query(models.TrBasNode).filter_by(bas_id=bas.id).delete()
            for node_id in nodes:
                basnode = models.TrBasNode()
                basnode.bas_id = bas.id
                basnode.node_id = node_id
                basnode.sync_ver = tools.gen_sync_ver()
                self.db.add(basnode)

            self.add_oplog(u'修改接入设备信息:%s' % bas.ip_addr)
            self.db.commit()
            dispatch.pub(CACHE_DELETE_EVENT, bas_cache_key(bas.nas_id), async=True)
            dispatch.pub(CACHE_DELETE_EVENT, bas_cache_key(bas.ip_addr), async=True)
            return bas
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='bas_update_error')
            self.last_error = u'修改接入设备失败:%s' % utils.safeunicode(err)
            return False

    @logparams
    def update_by_nasid(self, formdata, nodes = [], **kwargs):
        bas_id = self.db.query(models.TrBas.id).filter_by(ip_addr=formdata.nas_id).scalar()
        formdata.id = bas_id
        return self.update(formdata, nodes=nodes)

    @logparams
    def update_by_ipaddr(self, formdata, nodes = [], **kwargs):
        bas_id = self.db.query(models.TrBas.id).filter_by(ip_addr=formdata.ip_addr).scalar()
        formdata.id = bas_id
        return self.update(formdata, nodes=nodes)

    @logparams
    def delete(self, bas_id, **kwargs):
        try:
            self.db.query(models.TrBas).filter_by(id=bas_id).delete()
            self.add_oplog(u'删除接入设备信息:%s' % bas_id)
            self.db.commit()
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrBas.__tablename__, dict(id=bas_id)), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='bas_delete_error')
            self.last_error = u'删除接入设备失败:%s' % utils.safeunicode(err)
            return False

    @logparams
    def delete_by_nasid(self, nas_id, **kwargs):
        try:
            bas_id = self.db.query(models.TrBas.id).filter_by(nas_id=nas_id).scalar()
            self.db.query(models.TrBas).filter_by(id=bas_id).delete()
            self.add_oplog(u'删除接入设备信息:%s' % bas_id)
            self.db.commit()
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrBas.__tablename__, dict(id=bas_id)), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='bas_delete_error')
            self.last_error = u'删除接入设备失败:%s' % utils.safeunicode(err)
            return False

    @logparams
    def delete_by_ipaddr(self, ip_addr, **kwargs):
        try:
            bas_id = self.db.query(models.TrBas.id).filter_by(ip_addr=ip_addr).scalar()
            self.db.query(models.TrBas).filter_by(id=bas_id).delete()
            self.add_oplog(u'删除接入设备信息:%s' % bas_id)
            self.db.commit()
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrBas.__tablename__, dict(id=bas_id)), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='bas_delete_error')
            self.last_error = u'删除接入设备失败:%s' % utils.safeunicode(err)
            return False