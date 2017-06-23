#!/usr/bin/env python
# coding=utf-8
import os
import cyclone.web
from taurusxradius.taurusxlib import utils, logger, dispatch
from taurusxradius.modules.base import BaseHandler, authenticated
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules.system import config_forms
from taurusxradius.modules import models
from taurusxradius.modules.settings import *

@permit.suproute('/admin/config', u'系统配置管理', MenuSys, order=2.0, is_menu=True)

class ConfigHandler(BaseHandler):

    @authenticated
    def get(self):
        active = self.get_argument('active', 'system')
        system_form = config_forms.system_form()
        system_form.fill(self.settings.config.system)
        database_form = config_forms.database_form()
        hacfg_form = config_forms.hacfg_form()
        hacfg_form.fill(self.settings.config.ha)
        if 'DB_TYPE' in os.environ and 'DB_URL' in os.environ:
            self.settings.config['database']['dbtype'] = os.environ.get('DB_TYPE')
            self.settings.config['database']['dburl'] = os.environ.get('DB_URL')
        database_form.fill(self.settings.config.database)
        syslog_form = config_forms.syslog_form()
        syslog_form.fill(self.settings.config.syslog)
        self.render('config.html', active=active, system_form=system_form, database_form=database_form, syslog_form=syslog_form, hacfg_form=hacfg_form)


@permit.suproute('/admin/config/system/update', u'系统配置', u'系统管理', order=2.0001, is_menu=False)

class DefaultHandler(BaseHandler):

    @authenticated
    def post(self):
        if os.environ.get('DEMO_VER'):
            self.redirect('/admin/config?active=system')
            return
        config = self.settings.config
        config['system']['debug'] = int(self.get_argument('debug', 0))
        config['system']['tz'] = self.get_argument('tz')
        config['system']['license'] = self.get_argument('license', '')
        config.save()
        self.redirect('/admin/config?active=system')


@permit.suproute('/admin/config/database/update', u'数据库配置', u'系统管理', order=2.0002, is_menu=False)

class DatabaseHandler(BaseHandler):

    @authenticated
    def post(self):
        if os.environ.get('DEMO_VER'):
            self.redirect('/admin/config?active=database')
            return
        config = self.settings.config
        config['database']['echo'] = int(self.get_argument('echo'))
        config['database']['pool_size'] = int(self.get_argument('pool_size'))
        config['database']['pool_recycle'] = int(self.get_argument('pool_recycle'))
        config.save()
        self.redirect('/admin/config?active=database')


@permit.suproute('/admin/config/syslog/update', u'syslog 配置', u'系统管理', order=2.0003, is_menu=False)

class SyslogHandler(BaseHandler):

    @authenticated
    def post(self):
        if os.environ.get('DEMO_VER'):
            self.redirect('/admin/config?active=syslog')
            return
        self.settings.config['syslog']['enable'] = int(self.get_argument('enable'))
        self.settings.config['syslog']['server'] = self.get_argument('server')
        self.settings.config['syslog']['port'] = int(self.get_argument('port', 514))
        self.settings.config['syslog']['level'] = self.get_argument('level')
        self.settings.config.save()
        dispatch.pub(logger.EVENT_SETUP, self.settings.config)
        self.redirect('/admin/config?active=syslog')


@permit.suproute('/admin/config/secret/update', u'系统密钥更新', u'系统管理', order=2.0004, is_menu=False)

class SecretHandler(BaseHandler):

    @authenticated
    def post(self):
        new_secret = utils.gen_secret(32)
        new_aes = utils.AESCipher(key=new_secret)
        users = self.db.query(models.TrAccount)
        for user in users:
            oldpwd = self.aes.decrypt(user.password)
            user.password = new_aes.encrypt(oldpwd)

        self.application.aes = new_aes
        self.db.commit()
        self.settings.config['system']['secret'] = new_secret
        self.settings.config.save()
        self.render_json(code=0)


@permit.suproute('/admin/config/hacfg/update', u'高可用配置', u'系统管理', order=2.0003, is_menu=False)

class HaCfgHandler(BaseHandler):

    @authenticated
    def post(self):
        if os.environ.get('DEMO_VER'):
            self.redirect('/admin/config?active=hacfg')
            return
        self.settings.config['ha']['enable'] = int(self.get_argument('enable', 0))
        self.settings.config['ha']['interval'] = int(self.get_argument('interval', 5))
        self.settings.config['ha']['ping_interval'] = int(self.get_argument('ping_interval', 60))
        self.settings.config['ha']['master'] = self.get_argument('master')
        self.settings.config['ha']['slave'] = self.get_argument('slave')
        self.settings.config.save()
        self.redirect('/admin/config?active=hacfg')


@permit.suproute('/admin/license/upload')

class LicenseUploadHandler(BaseHandler):

    @authenticated
    def post(self):
        try:
            if os.environ.get('DEMO_VER'):
                self.write(u'这是一个演示版本，不提供此功能')
                return
            f = self.request.files['Filedata'][0]
            save_path = '/var/taurusxr/.license'
            tf = open(save_path, 'wb')
            licstr = f['body']
            start_tag = '----------START_TAURUSXEE_LICENSE----------'
            end_tag = '----------END_TAURUSXEE_LICENSE----------'
            if not licstr.startswith(start_tag):
                raise ValueError('license file lost start tag')
            if not licstr.endswith(end_tag):
                raise ValueError('license file lost end tag')
            body = licstr.replace(start_tag, '')
            body = body.replace(end_tag, '')
            tf.write(body.strip())
            tf.close()
            logger.info('write {0}'.format(save_path))
            self.write(u'上传完成，你需要重启一次服务来刷新授权')
        except Exception as err:
            logger.error(err)
            self.write(u'上传失败 %s' % utils.safeunicode(err))