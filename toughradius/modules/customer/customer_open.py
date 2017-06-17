#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
import random
import json
import string
from hashlib import md5
from toughradius.modules import models
from toughradius.modules.base import authenticated
from toughradius.modules.customer import customer_forms
from toughradius.modules.customer.customer import CustomerHandler
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch, logger
from toughradius.modules.settings import *
from toughradius.common import tools
from toughradius.modules.events.settings import ACCOUNT_OPEN_EVENT
from toughradius.modules.events.settings import ISSUES_ASSIGN_EVENT
from toughradius.modules.dbservice.customer_add import CustomerAdd

@permit.route('/admin/customer/fastopen', u'用户快速开户', MenuUser, order=1.10002, is_menu=True)

class CustomerFastOpenHandler(CustomerHandler):

    def get_form_params(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        products = [ (n.id, n.product_name) for n in self.get_opr_products() ]
        agencies = [ (n.id, n.agency_name) for n in self.get_opr_agencies() ]
        if not self.current_user.agency_id:
            agencies.insert(0, ('', ''))
        return (nodes, products, agencies)

    @authenticated
    def get(self):
        nodes, products, agencies = self.get_form_params()
        form = customer_forms.customer_fast_open_form(nodes, products, agencies)
        form.billing_type.set_value(1)
        return self.render('account_open_form.html', form=form)

    @authenticated
    def post(self):
        nodes, products, agencies = self.get_form_params()
        form = customer_forms.customer_fast_open_form(nodes, products, agencies)
        if not form.validates(source=self.get_params()):
            return self.render('account_open_form.html', form=form)
        try:
            cmanager = CustomerAdd(self.db, self.aes, operator=self.current_user)
            _params = dict(operator_name=self.current_user.username, operator_ip=self.current_user.ipaddr)
            ret = cmanager.add(form.d, **_params)
            if not ret:
                return self.render('account_open_form.html', form=form, msg=cmanager.last_error)
            self.db.commit()
        except Exception as err:
            logger.exception(err)
            return self.render_error(msg=u'用户开户失败，请联系管理员：ERROR：%s' % repr(err))

        CustomerBuildAccountHandler.set_session_number(form.d.account_rule, '')
        self.redirect(self.detail_url_fmt(form.d.account_number))


@permit.route('/admin/customer/open', u'用户正常开户', MenuUser, order=1.10001, is_menu=True)

class CustomerOpenHandler(CustomerHandler):

    def get_form_params(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        products = [ (n.id, n.product_name) for n in self.get_opr_products() ]
        agencies = [ (n.id, n.agency_name) for n in self.get_opr_agencies() ]
        if not self.current_user.agency_id:
            agencies.insert(0, ('', ''))
        return (nodes, products, agencies)

    @authenticated
    def get(self):
        nodes, products, agencies = self.get_form_params()
        form = customer_forms.customer_open_form(nodes, products, agencies)
        form.billing_type.set_value(1)
        return self.render('account_open_form.html', form=form)

    @authenticated
    def post(self):
        nodes, products, agencies = self.get_form_params()
        form = customer_forms.customer_open_form(nodes, products, agencies)
        if not form.validates(source=self.get_params()):
            return self.render('account_open_form.html', form=form)
        try:
            cmanager = CustomerAdd(self.db, self.aes, operator=self.current_user)
            _params = dict(operator_name=self.current_user.username, operator_ip=self.current_user.ipaddr)
            ret = cmanager.add(form.d, **_params)
            if not ret:
                return self.render('account_open_form.html', form=form, msg=cmanager.last_error)
        except Exception as err:
            logger.exception(err)
            return self.render_error(msg=u'用户开户失败，请联系管理员：ERROR：%s' % repr(err))

        CustomerBuildAccountHandler.set_session_number(form.d.account_rule, '')
        self.redirect(self.detail_url_fmt(form.d.account_number))


@permit.route('/admin/customer/account/build')

class CustomerBuildAccountHandler(CustomerHandler):
    session_accounts = {}

    @staticmethod
    def get_session_number(rule_id):
        return CustomerBuildAccountHandler.session_accounts.get('%s_session_account_number' % rule_id)

    @staticmethod
    def set_session_number(rule_id, account_number):
        CustomerBuildAccountHandler.session_accounts['%s_session_account_number' % rule_id] = account_number

    @authenticated
    def get(self):
        rule_id = self.get_argument('rule_id')
        session_account = CustomerBuildAccountHandler.get_session_number(rule_id)
        if not session_account:
            rule = self.db.query(models.TrAccountRule).get(rule_id)
            rule.user_sn = rule.user_sn + 1
            self.db.commit()
            account_number = '%s%s' % (rule.user_prefix, string.rjust(str(rule.user_sn), rule.user_suffix_len, '0'))
            CustomerBuildAccountHandler.set_session_number(rule_id, account_number)
        else:
            account_number = session_account
        passwd = ''.join([ random.choice(list('1234567890')) for _ in range(6) ])
        self.render_json(account=str(account_number), passwd=passwd)


@permit.route('/admin/customer/account/builders')

class CustomerNodeBuildersAccountHandler(CustomerHandler):

    @authenticated
    def get(self):
        area_id = self.get_argument('area_id')
        builders = []
        if area_id:
            builders = self.db.query(models.TrBuilder).filter(models.TrBuilder.id == models.TrAreaBuilder.builder_id, models.TrAreaBuilder.area_id == models.TrArea.id, models.TrArea.id == area_id)
        data = []
        for builder in builders:
            data.append(dict(builder_name=builder.builder_name))

        self.write(json.dumps(data, ensure_ascii=False))


@permit.route('/admin/customer/charges/update')

class CustomerChargesAccountHandler(CustomerHandler):

    @authenticated
    def get(self):
        product_id = self.get_argument('product_id')
        charges = self.db.query(models.TrCharges).filter(models.TrCharges.charge_code == models.TrProductCharges.charge_code, models.TrProductCharges.product_id == product_id)
        data = []
        for charge in charges:
            data.append(dict(charge_code=charge.charge_code, charge_name=charge.charge_name))

        self.write(json.dumps(data, ensure_ascii=False))


@permit.route('/admin/customer/area/update')

class CustomerAreaBuildersAccountHandler(CustomerHandler):

    @authenticated
    def get(self):
        node_id = self.get_argument('node_id')
        areas = self.db.query(models.TrArea).filter_by(node_id=node_id)
        data = []
        for area in areas:
            data.append(dict(area_name=area.area_name, area_id=area.id))

        self.write(json.dumps(data, ensure_ascii=False))


@permit.route('/admin/customer/address/build')

class CustomerAddreeeBuildHandler(CustomerHandler):

    @authenticated
    def get(self):
        area = self.db.query(models.TrArea).get(self.get_argument('area_id'))
        data = {'addr_prefix': area and area.addr_desc or ''}
        self.write(json.dumps(data, ensure_ascii=False))


@permit.route('/admin/customer/rule/update')

class CustomerAddreeeBuildHandler(CustomerHandler):

    @authenticated
    def get(self):
        node_id = self.get_argument('node_id')
        node = self.db.query(models.TrNode).get(node_id)
        data = {'account_rule': node.rule_id}
        self.write(json.dumps(data, ensure_ascii=False))


@permit.route('/admin/customer/batchopen', u'用户批量开户', MenuUser, order=1.10003, is_menu=True)

class CustomeBatchOpenHandler(CustomerHandler):

    def get_form_params(self):
        nodes = [ (n.id, n.node_name) for n in self.get_opr_nodes() ]
        products = [ (n.id, n.product_name) for n in self.get_opr_products() if n.product_policy not in (7,) ]
        return (nodes, products)

    @authenticated
    def get(self):
        nodes, products = self.get_form_params()
        form = customer_forms.customer_batch_open_form(nodes, products)
        form.opennum.set_value(100)
        form.user_prefix.set_value(datetime.datetime.now().strftime('%Y%m%d')[2:])
        form.suffix_len.set_value(4)
        form.start_num.set_value(1)
        return self.render('account_batch_open_form.html', form=form)

    @authenticated
    def post(self):
        nodes, products = self.get_form_params()
        form = customer_forms.customer_batch_open_form(nodes, products)
        if not form.validates(source=self.get_params()):
            return self.render('account_batch_open_form.html', form=form)
        try:
            cmanager = CustomerAdd(self.db, self.aes, operator=self.current_user)
            ret = cmanager.batch_add(form.d)
            if not ret:
                return self.render('account_batch_open_form.html', form=form, msg=cmanager.last_error)
        except Exception as err:
            logger.exception(err)
            return self.render_error(msg=u'用户开户失败，请联系管理员：ERROR：%s' % repr(err))

        self.redirect('/admin/customer')