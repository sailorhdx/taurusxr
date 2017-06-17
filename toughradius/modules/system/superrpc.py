#!/usr/bin/env python
# coding=utf-8
import os
from hashlib import md5
import cyclone.auth
import cyclone.escape
import cyclone.web
import traceback
from toughradius.toughlib import utils, dispatch, logger
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.settings import *
from toughradius.common import tools
if os.environ.get('TOUGHEE_SUPER_RPC') == 'true':
    state_descs = {0: u'<span class="label label-warning">未启动</span>',
     10: u'<span class="label label-info">启动中</span>',
     20: u'<span class="label label-success">运行中</span>',
     30: u'<span class="label label-danger">启动失败</span>',
     40: u'<span class="label label-warning">停止中</span>',
     100: u'<span class="label label-danger">已退出</span>',
     200: u'<span class="label label-danger">崩溃中</span>',
     1000: u'<span class="label label-warning">未知</span>'}
    name_desc = {'auth': u'认证监听服务',
     'acct': u'记账监听服务',
     'manage': u'管理控制台',
     'task': u'定时任务调度',
     'worker': u'Radius消息处理器',
     'ssportal': u'自助服务门户',
     'mpd': u'微信公众号服务',
     'syncd': u'数据同步服务',
     'redis': u'Redis缓存服务',
     'mongod': u'Mongodb数据库',
     'acsim': u'AC模拟器',
     'wlanportal': u'无线认证门户'}

    @permit.suproute('/admin/superrpc', u'系统服务管理', MenuSys, order=9.0, is_menu=True)

    class SuperProcsHandler(BaseHandler):

        def state_desc(self, statecode):
            return state_descs.get(int(statecode))

        def name_desc(self, name):
            if 'worker' in name:
                name = 'worker'
            if 'wlanportal' in name:
                name = 'wlanportal'
            return name_desc.get(str(name))

        @authenticated
        def get(self):
            procs = self.superrpc.supervisor.getAllProcessInfo()
            procs = [ p for p in procs if p.get('name') not in 'ops' ]
            self.render('superrpc.html', procs=procs)


    @permit.suproute('/admin/superrpc/restart', u'服务进程重启', MenuSys, order=9.0001, is_menu=False)

    class SuperProcRestartHandler(BaseHandler):

        @authenticated
        def get(self):
            try:
                if os.environ.get('DEMO_VER'):
                    self.render_json(code=1, msg=u'这是一个演示版本，不提供此功能')
                    return
                name = self.get_argument('name', None)
                if 'worker' in name:
                    name = 'worker:' + name
                ret = self.superrpc.system.multicall([{'methodName': 'supervisor.stopProcess',
                  'params': [name]}, {'methodName': 'supervisor.startProcess',
                  'params': [name]}])
                logger.info(ret)
            except:
                logger.error(traceback.format_exc())

            self.render_json(code=0, msg=u'重启服务完成')
            return


    @permit.suproute('/admin/superrpc/stop', u'服务进程停止', MenuSys, order=9.0002, is_menu=False)

    class SuperProcStopHandler(BaseHandler):

        @authenticated
        def get(self):
            try:
                if os.environ.get('DEMO_VER'):
                    self.render_json(code=1, msg=u'这是一个演示版本，不提供此功能')
                    return
                name = self.get_argument('name', None)
                if 'worker' in name:
                    name = 'worker:' + name
                ret = self.superrpc.supervisor.stopProcess(name)
                logger.info(ret)
            except:
                logger.error(traceback.format_exc())

            self.render_json(code=0, msg=u'停止服务完成')
            return


    @permit.suproute('/admin/superrpc/restartall', u'重启所有服务', MenuSys, order=9.0003, is_menu=False)

    class SuperProcRestartAllHandler(BaseHandler):

        @authenticated
        def get(self):
            try:
                if os.environ.get('DEMO_VER'):
                    self.render_json(code=1, msg=u'这是一个演示版本，不提供此功能')
                    return
                ret = self.superrpc.supervisor.restart()
                logger.info(ret)
            except:
                logger.error(traceback.format_exc())

            self.render_json(code=0, msg=u'正在重启服务')


    @permit.suproute('/admin/superrpc/reloadconfig', u'重载服务配置', MenuSys, order=9.0004, is_menu=False)

    class SuperProcReloadConfigHandler(BaseHandler):

        @authenticated
        def get(self):
            try:
                if os.environ.get('DEMO_VER'):
                    self.render_json(code=1, msg=u'这是一个演示版本，不提供此功能')
                    return
                ret = self.superrpc.supervisor.reloadConfig()
                logger.info(ret)
            except:
                logger.error(traceback.format_exc())

            self.render_json(code=0, msg=u'正在重载服务配置')


    @permit.suproute('/admin/superrpc/taillog', u'查询服务日志', MenuSys, order=9.0005, is_menu=False)

    class SuperProcTaillogHandler(BaseHandler):

        def log_query(self, logfile):
            if os.path.exists(logfile):
                with open(logfile) as f:
                    f.seek(0, 2)
                    if f.tell() > 16384:
                        f.seek(f.tell() - 16384)
                    else:
                        f.seek(0)
                    return cyclone.escape.xhtml_escape(utils.safeunicode(f.read())).replace('\n', '<br/>')
            else:
                return 'logfile %s not exist' % logfile

        @authenticated
        def get(self):
            try:
                if os.environ.get('DEMO_VER'):
                    self.render_json(code=0, msg=u'ok', log=u'这是一个演示版本，不提供此功能')
                    return
                try:
                    name = self.get_argument('name', '')
                    if 'worker' in name:
                        name = 'worker:worker0'
                    proc = self.superrpc.supervisor.getProcessInfo(name)
                    logfile = proc['stdout_logfile']
                except:
                    logfile = ''

                self.render_json(code=0, msg=u'ok', log=self.log_query(logfile))
            except:
                logger.error(traceback.format_exc())
                self.render_json(code=1, msg=u'err', log=u'read logger error:<br><br>%s' % traceback.format_exc())


@permit.suproute('/admin/superrpc/logdownload', u'服务日志下载', MenuSys, order=9.0007, is_menu=False)

class LoggerDownloadHandler(BaseHandler):

    @authenticated
    def get(self):
        try:
            if os.environ.get('DEMO_VER'):
                self.render_json(code=1, msg=u'这是一个演示版本，不提供此功能')
                return
            name = self.get_argument('name', '')
            if 'worker' in name:
                name = 'worker:worker0'
            proc = self.superrpc.supervisor.getProcessInfo(name)
            print proc
            logfile = proc['stdout_logfile']
        except:
            logfile = ''

        if os.path.exists(logfile):
            with open(logfile) as f:
                self.export_file(os.path.basename(logfile), f.read())
        else:
            self.write('logfile %s not exists' % logfile)
            self.finish()

    def export_file(self, filename, data):
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=' + filename)
        self.write(data)
        self.finish()