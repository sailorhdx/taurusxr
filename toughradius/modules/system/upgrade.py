#!/usr/bin/env python
# coding=utf-8
import os
import cyclone.auth
import cyclone.escape
import cyclone.web
import traceback
import json
from urllib import urlencode
from toughradius.toughlib import utils, dispatch, logger
from twisted.internet import defer
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.settings import *
from toughradius.common import tools
from cyclone import httpclient
import toughradius
import treq
import zipfile
import shutil
type_descs = {'dev': u'<span class="label label-info">开发版</span>',
 'stable': u'<span class="label label-success">稳定版</span>',
 'oem': u'<span class="label label-default">OEM 版</span>',
 'patch': u'<span class="label label-primary">升级补丁</span>'}

@permit.suproute('/api/v1/toughee/upgrade/metadata')

class UpgradeMetadataDemoHandler(BaseHandler):

    def get(self):
        self.render_json(code=0, metadata={})


@permit.suproute('/admin/upgrade', u'系统升级管理', MenuSys, order=10.0, is_menu=False)

class UpgradeMetadataHandler(BaseHandler):

    def type_desc(self, typestr):
        return type_descs.get(str(typestr))

    @defer.inlineCallbacks
    @authenticated
    def get(self):
        try:
            upgrade_url = self.settings.config.system.upgrade_url
            api_url = '{0}/api/v1/toughee/upgrade/metadata'.format(upgrade_url)
            api_token = yield tools.get_sys_token()
            params = dict(token=api_token)
            oemid = self.get_param_value('upgrade_oemid')
            if oemid:
                params['oemid'] = oemid
            param_str = urlencode(params)
            resp = yield httpclient.fetch(api_url + '?' + param_str, followRedirect=True)
            jobj = json.loads(resp.body)
            if jobj['code'] == 0:
                self.render('upgrade.html', metadata=jobj['metadata'])
            else:
                self.render_error(msg=utils.safeunicode(jobj['msg']))
        except Exception as err:
            logger.error(err)
            self.render_error(msg=repr(err))


@permit.suproute('/admin/upgrade/perform', u'系统版本升级', MenuSys, order=10.0001)

class UpgradePerformHandler(BaseHandler):

    @defer.inlineCallbacks
    @authenticated
    def get(self):
        try:
            if os.environ.get('DEMO_VER'):
                self.render_json(code=1, msg=u'这是一个演示版本，不提供此功能')
                return
            uid = self.get_argument('uid')
            upgrade_url = self.settings.config.system.upgrade_url
            api_url = '{0}/api/v1/toughee/upgrade/fetch/{1}'.format(upgrade_url, uid)
            api_token = yield tools.get_sys_token()
            params = dict(token=api_token)
            oemid = self.get_param_value('upgrade_oemid')
            if oemid:
                params['oemid'] = oemid
            param_str = urlencode(params)
            resp = yield treq.get(api_url + '?' + param_str, allow_redirects=True)
            if resp.code == 500:
                rbody = yield treq.content(resp)
                self.render_json(code=1, msg=u'获取升级包失败。服务器错误:<br> %s' % utils.safeunicode(rbody))
                return
            savepath = '/tmp/{0}.zip'.format(uid)
            _zipfile = open(savepath, 'wb')
            yield treq.collect(resp, _zipfile.write)
            _zipfile.close()
            backup_path = self.settings.config.database.backup_path
            backup_file = 'taurusxrdb_ubackup_%s.json.gz' % utils.gen_backep_id()
            self.db_backup.dumpdb(os.path.join(backup_path, backup_file))
            tools.upgrade_release(savepath)
            self.render_json(code=0, msg=u'升级完成,请重启所有服务')
        except Exception as err:
            logger.error(err)
            self.render_json(code=1, msg=utils.safeunicode(err))


@permit.suproute('/admin/upgrade/upload', u'上传版本升级', MenuSys, order=10.0004)

class UpgradeUploadHandler(BaseHandler):

    @authenticated
    def post(self):
        try:
            if os.environ.get('DEMO_VER'):
                self.write(u'这是一个演示版本，不提供上传升级功能')
                return
            f = self.request.files['Filedata'][0]
            savename = os.path.split(f['filename'])[1]
            savepath = '/tmp/{0}'.format(savename)
            logger.info('upload upgrade {}'.format(savepath), eslog=True)
            tf = open(savepath, 'wb')
            tf.write(f['body'])
            tf.close()
            backup_path = self.settings.config.database.backup_path
            backup_file = 'taurusxrdb_ubackup_%s.json.gz' % utils.gen_backep_id()
            self.db_backup.dumpdb(os.path.join(backup_path, backup_file))
            tools.upgrade_release(savepath)
            self.write(u'升级完成,请重启所有服务')
        except Exception as err:
            logger.error(err)
            self.write(u'升级失败 %s' % utils.safeunicode(err))