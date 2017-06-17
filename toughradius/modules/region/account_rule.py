#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.region import account_rule_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.modules.settings import *
from toughradius.common import tools

@permit.route('/admin/account_rule', u'账号生成规则', MenuNode, order=6.0, is_menu=True)

class AccountRuleListHandler(BaseHandler):

    @authenticated
    def get(self):
        rules = self.db.query(models.TrAccountRule)
        return self.render('account_rule_list.html', rules=rules)


@permit.suproute('/admin/account_rule/add', u'新增账号生成规则', MenuNode, order=6.0001)

class AccountRuleAddHandler(BaseHandler):

    @authenticated
    def get(self):
        form = account_rule_forms.account_rule_add_form()
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = account_rule_forms.account_rule_add_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        if self.db.query(models.TrAccountRule).filter_by(user_prefix=form.d.user_prefix).count() > 0:
            return self.render('base_form.html', form=form, msg=u'规则前缀已经存在')
        rule = models.TrAccountRule()
        rule.id = utils.get_uuid()
        rule.rule_name = form.d.rule_name
        rule.user_prefix = form.d.user_prefix
        rule.user_suffix_len = int(form.d.user_suffix_len)
        rule.sync_ver = tools.gen_sync_ver()
        self.db.add(rule)
        self.add_oplog(u'新增账号规则信息:%s' % utils.safeunicode(form.d.rule_name))
        self.db.commit()
        self.redirect('/admin/account_rule', permanent=False)


@permit.suproute('/admin/account_rule/update', u'修改账号生成规则', MenuNode, order=6.0002)

class AccountRuleUpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        rule_id = self.get_argument('rule_id')
        form = account_rule_forms.account_rule_update_form()
        rule = self.db.query(models.TrAccountRule).get(rule_id)
        form.fill(rule)
        self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        form = account_rule_forms.account_rule_update_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        rule = self.db.query(models.TrAccountRule).get(form.d.id)
        rule.rule_name = form.d.rule_name
        rule.user_prefix = form.d.user_prefix
        rule.user_suffix_len = int(form.d.user_suffix_len)
        rule.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'修改账号生成规则信息:%s' % utils.safeunicode(form.d.rule_name))
        self.db.commit()
        self.redirect('/admin/account_rule', permanent=False)


@permit.suproute('/admin/account_rule/delete', u'删除账号生成规则', MenuNode, order=6.0004)

class AccountRuleDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        rule_id = self.get_argument('rule_id')
        if self.db.query(models.TrNode).filter_by(rule_id=rule_id).count() > 0:
            return self.render_error(msg=u'账号生成规则已经被区域关联，请先取消关联。')
        self.db.query(models.TrAccountRule).filter_by(id=rule_id).delete()
        self.add_oplog(u'删除账号生成规则信息:%s' % rule_id)
        self.db.commit()
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAccountRule.__tablename__, dict(id=rule_id)), async=True)
        self.redirect('/admin/account_rule', permanent=False)