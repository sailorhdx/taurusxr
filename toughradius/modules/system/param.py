#!/usr/bin/env python
# coding=utf-8
import os, sys
import cyclone.auth
import cyclone.escape
import cyclone.web
import toughradius
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.system import param_forms
from toughradius.modules import models
from toughradius.toughlib.permit import permit
from toughradius.toughlib import dispatch, db_cache, logger, utils
from toughradius.modules.settings import *
from toughradius.common import tools

@permit.suproute('/admin/param', u'系统参数管理', MenuSys, is_menu=True, order=2.0005)

class ParamHandler(BaseHandler):

    @authenticated
    def get(self):
        active = self.get_argument('active', 'syscfg')
        sys_form = param_forms.sys_form()
        mail_form = param_forms.mail_form()
        rad_form = param_forms.rad_form()
        sms_form = param_forms.sms_form()
        alipay_form = param_forms.alipay_form()
        mps_form = param_forms.mps_form()
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        adconfig_form = param_forms.adconfig_form(nodes=nodes)
        fparam = {}
        for p in self.db.query(models.TrParam):
            fparam[p.param_name] = p.param_value

        for form in (sys_form,
         alipay_form,
         mps_form,
         mail_form,
         rad_form,
         sms_form,
         adconfig_form):
            form.fill(fparam)

        return self.render('param.html', active=active, sys_form=sys_form, alipay_form=alipay_form, mps_form=mps_form, mail_form=mail_form, sms_form=sms_form, rad_form=rad_form, adconfig_form=adconfig_form)


@permit.suproute('/admin/param/update', u'系统参数更新', MenuSys, order=2.0006)

class ParamUpdateHandler(BaseHandler):

    @authenticated
    def post(self):
        active = self.get_argument('active', 'syscfg')
        for param_name in self.get_params():
            if param_name in ('active', 'submit'):
                continue
            param = self.db.query(models.TrParam).filter_by(param_name=param_name).first()
            if not param:
                param = models.TrParam()
                param.param_name = param_name
                param.param_value = self.get_argument(param_name)
                param.sync_ver = tools.gen_sync_ver()
                self.db.add(param)
            else:
                param.param_value = self.get_argument(param_name)
            dispatch.pub(db_cache.CACHE_SET_EVENT, param_cache_key(param.param_name), param.param_value, 600)

        self.add_oplog(u'操作员(%s)修改参数' % self.current_user.username)
        self.db.commit()
        self.redirect('/admin/param?active=%s' % active)


@permit.suproute('/(MP_verify_.*\\.txt$)')

class DnsvHandler(BaseHandler):

    def get(self, vfile):
        file_path = os.path.join(os.path.dirname(toughradius.__file__), 'static/dnsv')
        _vfile = os.path.join(file_path, vfile)
        with open(_vfile) as fs:
            self.write(fs.read())


@permit.suproute('/admin/param/dnsv/upload')

class DnsvUploadHandler(BaseHandler):

    @authenticated
    def post(self):
        try:
            if os.environ.get('DEMO_VER'):
                self.write(u'这是一个演示版本，不提供此功能')
                return
            file_path = os.path.join(os.path.dirname(toughradius.__file__), 'static/dnsv')
            try:
                if not os.path.exists(file_path):
                    os.makedirs(file_path)
            except:
                pass

            f = self.request.files['Filedata'][0]
            filename = os.path.basename(utils.safestr(f['filename']))
            save_path = os.path.join(file_path, filename)
            tf = open(save_path, 'wb')
            filestr = f['body']
            tf.write(filestr.strip())
            tf.close()
            logger.info('write {0}'.format(save_path))
            self.write(u'上传完成')
        except Exception as err:
            logger.error(err)
            self.write(u'上传失败 %s' % utils.safeunicode(err))
