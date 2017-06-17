#!/usr/bin/env python
# coding=utf-8
import cyclone.web
import decimal
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.customer import issues_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.modules.settings import *
from toughradius.common import tools
from toughradius.modules.events.settings import ISSUES_ASSIGN_EVENT
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD

class IssuesBasicHandler(BaseHandler):

    def get_builders_by_account(self, account_number):
        builders = self.db.query(models.TrBuilder).filter(models.TrAccount.customer_id == models.TrCustomer.customer_id, models.TrAreaBuilder.builder_id == models.TrBuilder.id, models.TrCustomer.area_id == models.TrAreaBuilder.area_id)
        return [ (b.builder_name, '%s(%s)' % (b.builder_name, b.builder_phone)) for b in builders ]

    def get_all_builders(self):
        builders = self.db.query(models.TrBuilder)
        return [ (b.builder_name, '%s(%s)' % (b.builder_name, b.builder_phone)) for b in builders ]

    def get_builders_by_opr(self):
        areas = [ a.id for n, a in self.get_opr_areas() ]
        builders = self.db.query(models.TrBuilder).filter(models.TrNode.id == models.TrArea.node_id, models.TrAreaBuilder.area_id == models.TrArea.id, models.TrAreaBuilder.area_id.in_(areas))
        return [ (b.builder_name, '%s(%s)' % (b.builder_name, b.builder_phone)) for b in builders ]

    def get_builder(self, builder_name):
        return self.db.query(models.TrBuilder).filter_by(builder_name=builder_name).first()

    def pub_notify(self, issues):
        builder = self.get_builder(issues.builder_name)
        if not builder:
            return
        dispatch.pub(ISSUES_ASSIGN_EVENT, issues.account_number, builder_phone=builder.builder_phone, wechat_oid=builder.wechat_oid)


@permit.route('/admin/issues/list', u'用户工单管理', MenuUser, order=1.101, is_menu=True)

class IssuesListHandler(IssuesBasicHandler):

    @authenticated
    def get(self):
        self.post()

    @authenticated
    def post(self):
        builder_name = self.get_argument('builder_name', None)
        account_number = self.get_argument('account_number', None)
        issues_type = self.get_argument('issues_type', None)
        status = self.get_argument('status', None)
        agency_id = self.get_argument('agency_id', '').strip() or self.current_user.agency_id
        _query = self.db.query(models.TrIssues).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.account_number == models.TrIssues.account_number)
        if agency_id:
            _query = _query.filter(models.TrCustomer.agency_id == agency_id)
        if builder_name:
            _query = _query.filter_by(builder_name=builder_name)
        if account_number:
            _query = _query.filter_by(account_number=account_number)
        if issues_type:
            _query = _query.filter_by(issues_type=issues_type)
        if status:
            _query = _query.filter_by(status=status)
        _query = _query.order_by(models.TrIssues.date_time.desc())
        self.render('issues_list.html', page_data=self.get_page_data(_query), builders=self.get_builders_by_opr(), **self.get_params())
        return


@permit.route('/admin/issues/detail', u'用户工单详情', MenuUser, order=1.1011, is_menu=False)

class IssuesDetailHandler(IssuesBasicHandler):

    @authenticated
    def get(self):
        issues_id = self.get_argument('issues_id')
        issues = self.db.query(models.TrIssues).get(issues_id)
        issues_flows = self.db.query(models.TrIssuesFlow).filter_by(issues_id=issues_id)
        form = issues_forms.issues_process_form()
        form.issues_id.set_value(issues_id)
        colors = {0: 'label label-default',
         1: 'class="label label-info"',
         2: 'class="label label-warning"',
         3: 'class="label label-danger"',
         4: 'class="label label-success"'}
        return self.render('issues_detail.html', builders=self.get_builders_by_account(issues.account_number), issues=issues, issues_flows=issues_flows, form=form, colors=colors)


@permit.route('/admin/issues/add', u'创建用户工单', MenuUser, order=1.1012, is_menu=False)

class IssuesAddHandler(IssuesBasicHandler):

    @authenticated
    def get(self):
        account_number = self.get_argument('account_number')
        builders = self.get_builders_by_account(account_number)
        form = issues_forms.issues_add_form(builders)
        form.account_number.set_value(account_number)
        return self.render('base_form.html', form=form)

    @authenticated
    def post(self):
        builders = self.get_builders_by_account(self.get_argument('account_number'))
        form = issues_forms.issues_add_form(builders)
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        if self.db.query(models.TrAccount).filter_by(account_number=form.d.account_number).count() == 0:
            return self.render('base_form.html', form=form, msg=u'用户账号不存在')
        issues = models.TrIssues()
        issues.id = tools.gen_num_id(16)
        issues.account_number = form.d.account_number
        issues.issues_type = form.d.issues_type
        issues.content = form.d.content
        issues.builder_name = form.d.builder_name
        issues.status = 0
        issues.operator_name = self.current_user.username
        issues.date_time = utils.get_currtime()
        issues.sync_ver = tools.gen_sync_ver()
        self.db.add(issues)
        self.add_oplog(u'创建新工单:%s' % issues.id)
        self.db.commit()
        self.pub_notify(issues)
        self.redirect('/admin/issues/list')


@permit.route('/admin/issues/process', u'用户工单处理', MenuUser, order=1.1013, is_menu=False)

class IssuesProcessHandler(IssuesBasicHandler):

    @authenticated
    def post(self):
        form = issues_forms.issues_process_form()
        if not form.validates(source=self.get_params()):
            return self.render('base_form', form=form)
        iflow = models.TrIssuesFlow()
        iflow.id = tools.gen_num_id(16)
        iflow.issues_id = form.d.issues_id
        iflow.accept_time = utils.get_currtime()
        iflow.accept_status = form.d.accept_status
        iflow.accept_result = form.d.accept_result
        iflow.operator_name = self.current_user.username
        iflow.sync_ver = tools.gen_sync_ver()
        self.db.add(iflow)
        issues = self.db.query(models.TrIssues).get(iflow.issues_id)
        issues.status = iflow.accept_status
        issues.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'处理工单%s' % iflow.issues_id)
        self.db.commit()
        self.redirect('/admin/issues/detail?issues_id=%s' % iflow.issues_id)


@permit.route('/admin/issues/assign', u'用户工单指派', MenuUser, order=1.1014, is_menu=False)

class IssuesAssignHandler(IssuesBasicHandler):

    @authenticated
    def post(self):
        issues_id = self.get_argument('issues_id')
        builder_name = self.get_argument('builder_name')
        issues = self.db.query(models.TrIssues).get(issues_id)
        if builder_name == issues.builder_name:
            self.redirect('/admin/issues/detail?issues_id=%s' % issues_id)
            return
        issues.builder_name = builder_name
        issues.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'转派工单%s给%s' % (issues_id, builder_name))
        builder = self.get_builder(issues.builder_name)
        if builder:
            dispatch.pub(ISSUES_ASSIGN, issues.account_number, builder_phone=builder.builder_phone, wechat_oid=builder.wechat_oid, content=issues.content)
        self.db.commit()
        self.redirect('/admin/issues/detail?issues_id=%s' % issues_id)


@permit.route('/admin/issues/delete', u'用户工单删除', MenuUser, order=1.1015, is_menu=False)

class IssuesDeleteHandler(IssuesBasicHandler):

    @authenticated
    def get(self):
        issues_id = self.get_argument('issues_id')
        self.db.query(models.TrIssues).filter_by(id=issues_id).delete()
        self.db.query(models.TrIssuesFlow).filter_by(issues_id=issues_id)
        self.add_oplog(u'删除工单%s' % issues_id)
        self.db.commit()
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrIssues.__tablename__, dict(id=issues_id)), async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrIssuesFlow.__tablename__, dict(issues_id=issues_id)), async=True)
        self.redirect('/admin/issues/list')