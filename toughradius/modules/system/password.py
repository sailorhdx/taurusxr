#!/usr/bin/env python
# coding=utf-8
import os
from hashlib import md5
from toughradius.toughlib import utils
from toughradius.modules.base import BaseHandler, MenuSys, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.system import password_forms
from toughradius.modules.settings import *
from toughradius.common import tools

@permit.route('/admin/password')

class PasswordUpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        form = password_forms.password_update_form()
        form.fill(tr_user=self.current_user.username)
        return self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        if os.environ.get('DEMO_VER'):
            return self.redirect('/admin')
        form = password_forms.password_update_form()
        if not form.validates(source=self.get_params()):
            self.render('base_form.html', form=form)
            return
        if form.d.tr_user_pass != form.d.tr_user_pass_chk:
            self.render('base_form.html', form=form, msg=u'确认密码不一致')
            return
        opr = self.db.query(models.TrOperator).filter_by(operator_name=self.current_user.username).first()
        opr.operator_pass = md5(form.d.tr_user_pass).hexdigest()
        opr.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'修改%s密码 ' % self.current_user.username)
        self.db.commit()
        self.redirect('/admin')