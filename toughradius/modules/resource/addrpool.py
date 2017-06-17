#!/usr/bin/env python
# coding=utf-8
import time
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.resource import addrpool_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.toughlib import redis_cache
from toughradius.modules.settings import *
from toughradius.modules.events.settings import ROSSYNC_ADD_POOL
from toughradius.modules.events.settings import ROSSYNC_SET_POOL
from toughradius.modules.events.settings import ROSSYNC_DEL_POOL
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.common import tools

@permit.route('/admin/addrpool', u'地址池管理', MenuRes, order=2.0001, is_menu=True)

class AddrPoolListHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('addrpool_list.html', pool_list=self.db.query(models.TrAddrPool))


@permit.suproute('/admin/addrpool/add', u'新增地址池', MenuRes, order=2.0011)

class AddrPoolAddHandler(BaseHandler):

    @authenticated
    def get(self):
        form = addrpool_forms.pool_add_form()
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = addrpool_forms.pool_add_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        if self.db.query(models.TrAddrPool.id).filter_by(pool_name=form.d.pool_name).count() > 0:
            return self.render('base_form.html', form=form, msg=u'地址池名称已经存在')
        pool = models.TrAddrPool()
        pool.id = utils.get_uuid()
        pool.pool_name = form.d.pool_name
        pool.start_ip = form.d.start_ip
        pool.end_ip = form.d.end_ip
        pool.next_pool = form.d.next_pool or ''
        pool.sync_ver = tools.gen_sync_ver()
        self.db.add(pool)
        self.add_oplog(u'新增地址池信息:%s' % pool.pool_name)
        self.db.commit()
        dispatch.pub(ROSSYNC_ADD_POOL, pool.pool_name, '%s-%s' % (pool.start_ip, pool.end_ip), pool.next_pool, async=True)
        self.redirect('/admin/addrpool', permanent=False)


@permit.suproute('/admin/addrpool/update', u'修改地址池', MenuRes, order=2.0012)

class AddrPoolUpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        pool_id = self.get_argument('pool_id')
        form = addrpool_forms.pool_update_form()
        form.fill(self.db.query(models.TrAddrPool).get(pool_id))
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = addrpool_forms.pool_update_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        pool = self.db.query(models.TrAddrPool).get(form.d.id)
        pool.start_ip = form.d.start_ip
        pool.end_ip = form.d.end_ip
        pool.next_pool = form.d.next_pool or ''
        pool.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'修改地址池信息:%s' % pool.pool_name)
        self.db.commit()
        dispatch.pub(ROSSYNC_SET_POOL, pool.pool_name, '%s-%s' % (pool.start_ip, pool.end_ip), pool.next_pool, async=True)
        self.redirect('/admin/addrpool', permanent=False)


@permit.suproute('/admin/addrpool/delete', u'删除地址池', MenuRes, order=2.0013)

class AddrPoolDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        pool_id = self.get_argument('pool_id')
        pool_name = self.db.query(models.TrAddrPool.pool_name).filter_by(id=pool_id).scalar()
        self.db.query(models.TrAddrPool).filter_by(id=pool_id).delete()
        self.add_oplog(u'删除地址池信息:%s' % pool_name)
        self.db.commit()
        dispatch.pub(ROSSYNC_DEL_POOL, pool_name, async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAddrPool.__tablename__, dict(id=pool_id)), async=True)
        self.redirect('/admin/addrpool', permanent=False)