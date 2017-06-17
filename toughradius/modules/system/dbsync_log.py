#!/usr/bin/env python
# coding=utf-8
import os
import cyclone.auth
import cyclone.escape
import cyclone.web
from toughradius.modules import models
from toughradius.common import tools
from toughradius.modules.base import BaseHandler, MenuSys, authenticated
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.modules.settings import *
if 'HASYNC_DISABLE' not in os.environ:

    @permit.suproute('/admin/dbsync/log', u'数据同步管理', MenuSys, order=5.0, is_menu=True)

    class DbsyncLogListHandler(BaseHandler):

        @authenticated
        def get(self):
            self.post()

        @authenticated
        def post(self):
            action = self.get_argument('action', '')
            query_begin_time = self.get_argument('query_begin_time', '')
            query_end_time = self.get_argument('query_end_time', '')
            sync_status = self.get_argument('sync_status', '')
            _query = self.db.query(models.TrRepliSyncStatus)
            if action:
                _query = _query.filter(models.TrRepliSyncStatus.action == action)
            if sync_status:
                _query = _query.filter(models.TrRepliSyncStatus.sync_status == sync_status)
            if query_begin_time:
                _query = _query.filter(models.TrRepliSyncStatus.operate_time >= query_begin_time + ' 00:00:00')
            if query_end_time:
                _query = _query.filter(models.TrRepliSyncStatus.operate_time <= query_end_time + ' 23:59:59')
            _query = _query.order_by('create_time desc')
            return self.render('dbsync_log_list.html', page_data=self.get_page_data(_query), **self.get_params())


    @permit.suproute('/admin/dbsync/syncall', u'同步所有数据', MenuSys, order=5.0001, is_menu=False)

    class DbsyncAllHandler(BaseHandler):

        @authenticated
        def post(self):
            if os.environ.get('DEMO_VER'):
                self.render_json(code=1, msg=u'这是一个演示版本，不提供此功能')
                return
            for table in models.SYNC_TABLES:
                for o in self.db.query(table):
                    if hasattr(o, 'sync_ver'):
                        o.sync_ver = tools.gen_sync_ver()

                self.db.commit()

            self.render_json(code=0, msg=u'操作已发送, 同步未完成之前请勿重复操作。')