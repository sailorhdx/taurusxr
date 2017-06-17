#!/usr/bin/env python
# coding=utf-8
import os
import os.path
import cyclone.auth
import cyclone.escape
import cyclone.web
from toughradius.toughlib import utils, dispatch, logger
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules.settings import *

@permit.suproute('/admin/backup', u'数据备份管理', MenuSys, order=5.0001, is_menu=True)

class BackupHandler(BaseHandler):

    @authenticated
    def get(self):
        backup_path = self.settings.config.database.backup_path
        try:
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
        except:
            pass

        flist = os.listdir(backup_path)
        flist.sort(reverse=True)
        return self.render('backup_db.html', backups=flist[:100], backup_path=backup_path)


@permit.suproute('/admin/backup/dump', u'备份数据', MenuSys, order=5.0002)

class DumpHandler(BaseHandler):

    @authenticated
    def post(self):
        if os.environ.get('DEMO_VER'):
            self.render_json(code=1, msg=u'这是一个演示版本，不支持此功能')
            return
        backup_path = self.settings.config.database.backup_path
        backup_file = 'toughradius_db_%s.json.gz' % utils.gen_backep_id()
        try:
            self.db_backup.dumpdb(os.path.join(backup_path, backup_file))
            return self.render_json(code=0, msg='backup done!')
        except Exception as err:
            dispatch.pub(logger.EVENT_EXCEPTION, err)
            return self.render_json(code=1, msg='backup fail! %s' % err)


@permit.suproute('/admin/backup/restore', u'恢复数据', MenuSys, order=5.0003)

class RestoreHandler(BaseHandler):

    @authenticated
    def post(self):
        if os.environ.get('DEMO_VER'):
            self.render_json(code=1, msg=u'这是一个演示版本，不支持此功能')
            return
        backup_path = self.settings.config.database.backup_path
        backup_file = 'toughradius_db_%s.before_restore.json.gz' % utils.gen_backep_id()
        rebakfs = self.get_argument('bakfs')
        try:
            self.db_backup.dumpdb(os.path.join(backup_path, backup_file))
            if 'trv1' in rebakfs:
                self.db_backup.restoredbv1(os.path.join(backup_path, rebakfs))
            else:
                self.db_backup.restoredb(os.path.join(backup_path, rebakfs))
            return self.render_json(code=0, msg='restore done!')
        except Exception as err:
            dispatch.pub(logger.EVENT_EXCEPTION, err)
            return self.render_json(code=1, msg='restore fail! %s' % err)


@permit.suproute('/admin/backup/delete', u'删除数据', MenuSys, order=5.0004)

class DeleteHandler(BaseHandler):

    @authenticated
    def post(self):
        if os.environ.get('DEMO_VER'):
            self.write(u'这是一个演示版本，不提供此功能')
            return
        backup_path = self.settings.config.database.backup_path
        bakfs = self.get_argument('bakfs')
        try:
            os.remove(os.path.join(backup_path, bakfs))
            return self.render_json(code=0, msg='delete done!')
        except Exception as err:
            dispatch.pub(logger.EVENT_EXCEPTION, err)
            return self.render_json(code=1, msg='delete fail! %s' % err)


@permit.suproute('/admin/backup/upload', u'上传数据', MenuSys, order=5.0004)

class UploadHandler(BaseHandler):

    @authenticated
    def post(self):
        try:
            if os.environ.get('DEMO_VER'):
                self.write(u'这是一个演示版本，不提供上传功能')
                return
            f = self.request.files['Filedata'][0]
            savename = os.path.split(f['filename'])[1]
            save_path = os.path.join(self.settings.config.database.backup_path, savename)
            logger.info('upload dbfile {}'.format(save_path), eslog=True)
            tf = open(save_path, 'wb')
            tf.write(f['body'])
            tf.close()
            self.write('upload success')
        except Exception as err:
            dispatch.pub(logger.EVENT_EXCEPTION, err)
            self.write('upload fail %s' % str(err))


@permit.suproute('/admin/backup/download/(.*)')

class downloadHandler(BaseHandler):

    def get(self, filename):
        if os.environ.get('DEMO_VER'):
            self.write(u'这是一个演示版本，不提供此功能')
            return
        if not self.current_user or self.current_user.opr_type > 0:
            return self.render_error(msg=u'未授权的访问')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=' + filename)
        file_path = os.path.join(self.settings.config.database.backup_path, filename)
        with open(file_path, 'rb') as df:
            for line in df:
                self.write(line)

        self.finish()