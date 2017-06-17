#!/usr/bin/env python
# coding=utf-8
import json
import os
from toughradius.toughlib import utils, dispatch
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib import logger
from toughradius.modules import models
from toughradius.modules.events.event_basic import BasicEvent
from toughradius.common import tools
from twisted.internet import reactor

class DbSyncStatusEvent(BasicEvent):

    def obj2json(self, mdl):
        if isinstance(mdl, (list, dict)):
            return json.dumps(mdl, ensure_ascii=False)
        if hasattr(mdl, '__table__'):
            data = {}
            for c in mdl.__table__.columns:
                data[c.name] = getattr(mdl, c.name)

            return json.dumps(data)

    def event_add_sync_status(self, sync_obj, **kwargs):
        if 'HASYNC_DISABLE' in os.environ:
            return

        def do_async():
            try:
                with make_db(self.db) as db:
                    _status = models.TrRepliSyncStatus()
                    _status.id = utils.get_uuid()
                    _status.table_name = sync_obj.table_name
                    _status.action = sync_obj.action
                    _status.sync_status = 0
                    _status.sync_times = 0
                    _status.error = ''
                    _status.pkeys = sync_obj.pkeys
                    _status.content = sync_obj.content
                    _status.create_time = utils.get_currtime()
                    _status.last_sync = _status.create_time
                    _status.sync_ver = sync_obj.sync_ver or tools.gen_sync_ver()
                    db.add(_status)
                    db.commit()
            except Exception as err:
                import traceback
                traceback.print_exc()

        reactor.callLater(0.1, do_async)


def __call__(dbengine = None, mcache = None, aes = None, **kwargs):
    return DbSyncStatusEvent(dbengine=dbengine, mcache=mcache, aes=aes, **kwargs)