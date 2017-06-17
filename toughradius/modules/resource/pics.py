#!/usr/bin/env python
# coding=utf-8
import os
import time
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch, logger
from toughradius.modules.settings import *
from toughradius.common import tools, safefile
import toughradius

@permit.suproute('/admin/pics', u'图片文件管理', MenuRes, order=9.0, is_menu=True)

class PicListHandler(BaseHandler):

    @authenticated
    def get(self):
        try:
            pic_path = os.path.join(os.path.dirname(toughradius.__file__), 'static/pics')
            if not os.path.exists(pic_path):
                os.makedirs(pic_path)
        except:
            pass

        flist = os.listdir(pic_path)
        flist.sort(reverse=True)
        self.render('pics.html', pic_path=pic_path, flist=flist)


@permit.suproute('/admin/pic/upload', u'上传图片', MenuRes, order=9.0004)

class PicsUploadHandler(BaseHandler):

    def post(self):
        try:
            pic_path = os.path.join(os.path.dirname(toughradius.__file__), 'static/pics')
            try:
                if not os.path.exists(pic_path):
                    os.makedirs(pic_path)
            except:
                pass

            f = self.request.files['Filedata'][0]
            filename = os.path.basename(utils.safestr(f['filename']))
            savename = 'pic{0}_{1}'.format(tools.gen_num_id(13), filename)
            save_path = os.path.join(pic_path, savename)
            tf = open(save_path, 'wb')
            tf.write(f['body'])
            tf.close()
            if not safefile.isimg(save_path):
                os.remove(save_path)
                logger.error('error upload file %s' % save_path)
                self.write(u'上传的文件不是图片类型')
                return
            logger.info('write {0}'.format(save_path))
            self.write(u'upload ok')
        except Exception as err:
            logger.error(err)
            self.write(u'上传失败 %s' % utils.safeunicode(err))


@permit.suproute('/admin/pic/delete', u'删除图片', MenuRes, order=9.0004)

class PicDeleteHandler(BaseHandler):

    @authenticated
    def post(self):
        pic_path = os.path.join(os.path.dirname(toughradius.__file__), 'static/pics')
        picfs = self.get_argument('picfs')
        try:
            filepath = os.path.join(pic_path, os.path.basename(picfs))
            if os.path.exists(filepath):
                os.remove(filepath)
                return self.render_json(code=0, msg='delete done!')
            return self.render_json(code=1, msg='file %s not exists' % filepath)
        except Exception as err:
            logger.exception(err)
            return self.render_json(code=1, msg='delete fail! %s' % err)