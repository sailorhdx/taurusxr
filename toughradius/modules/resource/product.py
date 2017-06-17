#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.resource import product_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, logger
from toughradius.modules.settings import *
from toughradius.modules.dbservice.product_service import ProductService
product_add_actions = ((u'预付费包日', '/admin/product/add?product_policy=9'),
 (u'买断包日', '/admin/product/add?product_policy=10'),
 (u'预付费包月', '/admin/product/add?product_policy=0'),
 (u'后付费包月', '/admin/product/add?product_policy=8'),
 (u'买断包月', '/admin/product/add?product_policy=2'),
 (u'买断时长', '/admin/product/add?product_policy=3'),
 (u'买断流量', '/admin/product/add?product_policy=5'))
product_policys = {PPMonth: u'预付费包月',
 APMonth: u'后付费包月',
 PPTimes: u'预付费时长',
 BOMonth: u'买断包月',
 BOTimes: u'买断时长',
 PPFlow: u'预付费流量',
 BOFlows: u'买断流量',
 PPMFlows: u'预付费流量包月',
 PPDay: u'预付费包日',
 BODay: u'买断包日'}

@permit.route('/admin/product', u'资费套餐管理', MenuRes, order=3.0, is_menu=True)

class ProductListHandler(BaseHandler):

    @authenticated
    def get(self):
        query = self.get_opr_products()
        self.render('product_list.html', product_add_actions=product_add_actions, product_policys=product_policys, node_list=self.db.query(models.TrNode), products=query)


@permit.suproute('/admin/product/add', u'新增资费套餐', MenuRes, order=3.0001)

class ProductAddListHandler(BaseHandler):

    @authenticated
    def get(self):
        product_policy = self.get_argument('product_policy', 0)
        charges = [ (p.charge_code, p.charge_name) for p in self.db.query(models.TrCharges) ]
        pools = [('', '')] + [ (p.pool_name, p.pool_name) for p in self.db.query(models.TrAddrPool) ]
        form = product_forms.product_add_form(product_policy, charges=charges, pools=pools)
        form.product_policy.set_value(int(product_policy))
        form.concur_number.set_value(1)
        form.product_id.set_value(utils.get_uuid())
        form.free_auth.set_value(0)
        form.free_auth_uprate.set_value(0)
        form.free_auth_downrate.set_value(0)
        self.render('product_form.html', form=form)

    @authenticated
    def post(self):
        product_policy = self.get_argument('product_policy', 0)
        pools = [('', '')] + [ (p.pool_name, p.pool_name) for p in self.db.query(models.TrAddrPool) ]
        charges = [ (p.charge_code, p.charge_name) for p in self.db.query(models.TrCharges) ]
        form = product_forms.product_add_form(product_policy, charges=charges, pools=pools)
        if not form.validates(source=self.get_params()):
            return self.render('product_form.html', form=form)
        try:
            manager = ProductService(self.db, self.aes, operator=self.current_user)
            _params = dict(operator_name=self.current_user.username, operator_ip=self.current_user.ipaddr, item_charges=self.get_arguments('product_charges'))
            ret = manager.add(form.d, **_params)
            if not ret:
                return self.render('product_form.html', form=form, msg=manager.last_error)
        except Exception as err:
            logger.exception(err)
            return self.render_error(msg=u'操作失败，请联系管理员：ERROR：%s' % repr(err))

        self.redirect('/admin/product', permanent=False)


@permit.suproute('/admin/product/update', u'修改资费套餐', MenuRes, order=3.0002)

class ProductUpdateListHandler(BaseHandler):

    def get_addr_pool(self, pid):
        return self.db.query(models.TrProductAttr.attr_value).filter_by(product_id=pid, attr_name='Framed-Pool').scalar()

    @authenticated
    def get(self):
        product_id = self.get_argument('product_id')
        pools = [('', '')] + [ (p.pool_name, p.pool_name) for p in self.db.query(models.TrAddrPool) ]
        charges = [ (p.charge_code, p.charge_name) for p in self.db.query(models.TrCharges) ]
        pcharges = self.db.query(models.TrProductCharges).filter_by(product_id=product_id)
        product = self.db.query(models.TrProduct).get(product_id)
        form = product_forms.product_update_form(product.product_policy, charges=charges, pools=pools)
        form.fill(product)
        form.product_charges.set_value([ c.charge_code for c in pcharges ])
        form.addr_pool.set_value(self.get_addr_pool(product_id))
        form.product_policy_name.set_value(product_forms.product_policy[product.product_policy])
        form.fee_times.set_value(utils.sec2hour(product.fee_times))
        form.fee_flows.set_value(utils.kb2gb(product.fee_flows))
        form.input_max_limit.set_value(utils.bps2mbps(product.input_max_limit))
        form.output_max_limit.set_value(utils.bps2mbps(product.output_max_limit))
        form.fee_price.set_value(utils.fen2yuan(product.fee_price))
        form.free_auth_uprate.set_value(utils.bps2mbps(product.free_auth_uprate))
        form.free_auth_downrate.set_value(utils.bps2mbps(product.free_auth_downrate))
        attrs = self.db.query(models.TrProductAttr).filter_by(product_id=product.id, attr_type=0)
        for attr in attrs:
            if hasattr(form, attr.attr_name):
                getattr(form, attr.attr_name).set_value(attr.attr_value)

        return self.render('product_form.html', form=form)

    @authenticated
    def post(self):
        product_policy = self.get_argument('product_policy', 0)
        pools = [('', '')] + [ (p.pool_name, p.pool_name) for p in self.db.query(models.TrAddrPool) ]
        charges = [ (p.charge_code, p.charge_name) for p in self.db.query(models.TrCharges) ]
        form = product_forms.product_update_form(product_policy, charges=charges, pools=pools)
        if not form.validates(source=self.get_params()):
            return self.render('product_form.html', form=form)
        try:
            manager = ProductService(self.db, self.aes, operator=self.current_user)
            _params = dict(operator_name=self.current_user.username, operator_ip=self.current_user.ipaddr, item_charges=self.get_arguments('product_charges'))
            ret = manager.update(form.d, **_params)
            if not ret:
                return self.render('product_form.html', form=form, msg=manager.last_error)
        except Exception as err:
            logger.exception(err)
            self.db.rollback()
            return self.render_error(msg=u'操作失败，请联系管理员：ERROR：%s' % repr(err))

        self.redirect('/admin/product', permanent=False)


@permit.suproute('/admin/product/delete', u'删除资费套餐', MenuRes, order=3.0003)

class ProductDeleteListHandler(BaseHandler):

    @authenticated
    def get(self):
        product_id = self.get_argument('product_id')
        try:
            manager = ProductService(self.db, self.aes, operator=self.current_user)
            _params = dict(operator_name=self.current_user.username, operator_ip=self.current_user.ipaddr)
            ret = manager.delete(product_id, **_params)
            if not ret:
                return self.render_error(msg=manager.last_error)
        except Exception as err:
            logger.exception(err)
            self.db.rollback()
            return self.render_error(msg=u'操作失败，请联系管理员：ERROR：%s' % repr(err))

        self.redirect('/admin/product', permanent=False)


@permit.route('/admin/product/detail', u'资费详情', MenuRes, order=3.0004)

class ProductDeleteListHandler(BaseHandler):

    @authenticated
    def get(self):
        product_id = self.get_argument('product_id')
        product = self.db.query(models.TrProduct).get(product_id)
        if not product:
            return self.render_error(msg=u'资费不存在')
        product_charges = self.db.query(models.TrCharges).filter(models.TrCharges.charge_code == models.TrProductCharges.charge_code, models.TrProductCharges.product_id == product_id)
        product_attrs = self.db.query(models.TrProductAttr).filter_by(product_id=product_id)
        return self.render('product_detail.html', product_policys=product_policys, product_charges=product_charges, product=product, product_attrs=product_attrs)