#!/usr/bin/env python
#coding:utf-8
import os
import json
import subprocess
import datetime
import time
import os.path
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.txradius import statistics
from toughradius.toughlib.permit import permit
from sqlalchemy.sql import func
from toughradius.toughlib import utils
from collections import deque
from toughradius.modules import models
from toughradius.modules.settings import *
from toughradius.common import tools
try:
    import psutil
except:
    import traceback
    traceback.print_exc()

@permit.route('/admin/cache/clean')

class CacheClearHandler(BaseHandler):

    def get(self):
        self.cache.clean()
        self.render_json(msg=u'刷新缓存完成')


@permit.route('/admin/trace/clean')

class TraceClearHandler(BaseHandler):

    def get(self):
        self.logtrace.clean()
        self.render_json(msg=u'刷新系统消息缓存完成')


@permit.route('/admin/dashboard')

class DashboardHandler(BaseHandler):

    def bb2gb(self, ik):
        _kb = decimal.Decimal(ik or 0)
        _mb = _kb / decimal.Decimal(1000000000)
        return str(_mb.quantize(decimal.Decimal('1.00')))

    def bar_style(self, value):
        val = int(value)
        if val <= 50:
            return 'success'
        if val > 50 and val < 90:
            return 'warning'
        if val >= 90:
            return 'danger'

    def cache_rate(self):
        rate = decimal.Decimal(self.cache.hit_total * 100.0 / (self.cache.get_total + 0.0001))
        return str(rate.quantize(decimal.Decimal('1.00')))

    def get_disk_use(self):
        try:
            disks = [ (p, psutil.disk_usage(p)) for p in [ a.mountpoint for a in psutil.disk_partitions() ] ]
            return disks
        except:
            return []

    @authenticated
    def get(self):
        if os.environ.get('DEMO_VER'):
            sys_uuid = '1rt352ff88f31d95df7d4ae3f8c276eg'
        else:
            sys_uuid = tools.get_sys_uuid()
        cpuuse = psutil.cpu_percent(interval=None, percpu=True)
        memuse = psutil.virtual_memory()
        diskuse = self.get_disk_use()
        online_count = self.db.query(models.TrOnline.id).count()
        user_total = self.db.query(models.TrAccount.account_number).filter_by(status=1).count()
        self.render('index.html', config=self.settings.config, cpuuse=cpuuse, memuse=memuse, diskuse=diskuse, online_count=online_count, user_total=user_total, sys_uuid=sys_uuid, cache_rate=self.cache_rate, hadb_status=self.cache.get(hadb_sync_status_cache_key), hadb_count=self.cache.get(hadb_sync_count_cache_key))
        return


class ComplexEncoder(json.JSONEncoder):

    def default(self, obj):
        if type(obj) == deque:
            return [ i for i in obj ]
        return json.JSONEncoder.default(self, obj)


@permit.route('/admin/dashboard/msgstat')

class MsgStatHandler(BaseHandler):

    @authenticated
    def get(self):
        resp = json.dumps(self.cache.get(radius_statcache_key), cls=ComplexEncoder, ensure_ascii=False)
        self.write(resp)


def default_start_end():
    day_code = datetime.datetime.now().strftime('%Y-%m-%d')
    begin = datetime.datetime.strptime('%s 00:00:00' % day_code, '%Y-%m-%d %H:%M:%S')
    end = datetime.datetime.strptime('%s 23:59:59' % day_code, '%Y-%m-%d %H:%M:%S')
    return (time.mktime(begin.timetuple()), time.mktime(end.timetuple()))


@permit.route('/admin/dashboard/onlinestat')

class OnlineStatHandler(BaseHandler):

    @authenticated
    def get(self):
        olstat = self.cache.get(online_statcache_key) or []
        self.render_json(code=0, data=[{'name': u'所有区域',
          'data': olstat}])


@permit.route('/admin/dashboard/flowstat')

class FlowStatHandler(BaseHandler):

    def sizedesc(self, ik):
        _kb = decimal.Decimal(ik or 0)
        _mb = _kb / decimal.Decimal(1024)
        return str(_mb.quantize(decimal.Decimal('1.000')))

    @authenticated
    def get(self):
        flow_stat = self.cache.get(flow_statcache_key) or {}
        _idata = [ (_time, float(self.sizedesc(bb))) for _time, bb in flow_stat.get('input_stat', []) if bb > 0 ][-512:]
        _odata = [ (_time, float(self.sizedesc(bb))) for _time, bb in flow_stat.get('output_stat', []) if bb > 0 ][-512:]
        in_data = {'name': u'上行流量',
         'data': _idata}
        out_data = {'name': u'下行流量',
         'data': _odata}
        self.render_json(code=0, data=[in_data, out_data])