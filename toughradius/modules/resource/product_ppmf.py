#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.resource import product_ppmf_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, logger
from toughradius.modules.settings import *
from toughradius.modules.dbservice.product_service import ProductService
from toughradius.common import tools

@permit.suproute('/admin/product/ppmf/add', u'新增预付费流量包月资费', MenuRes, order=3.0001)

class ProductPpmfAddListHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('product_ppmf_form.html', form=product_ppmf_forms.ppmflow_product_add_form())

    @authenticated
    def post(self):
        form = product_ppmf_forms.ppmflow_product_add_form()
        if not form.validates(source=self.get_params()):
            return self.render('product_ppmf_form.html', form=form)
        try:
            manager = ProductService(self.db, self.aes, operator=self.current_user)
            _params = dict(operator_name=self.current_user.username, operator_ip=self.current_user.ipaddr)
            ret = manager.add_ppmf(form.d, **_params)
            if ret:
                self.db.commit()
        except Exception as err:
            logger.exception(err)
            self.db.rollback()
            return self.render_error(msg=u'操作失败，请联系管理员：ERROR：%s' % repr(err))

        self.redirect('/admin/product', permanent=False)


@permit.suproute('/admin/product/ppmf/update', u'修改预付费流量包月资费', MenuRes, order=3.0002)

class ProductUpdateListHandler(BaseHandler):

    @authenticated
    def get(self):
        product_id = self.get_argument('product_id')
        form = product_ppmf_forms.ppmflow_product_update_form()
        product = self.db.query(models.TrProduct).get(product_id)
        form.fill(product)
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

        return self.render('product_ppmf_form.html', form=form)

    @authenticated
    def post(self):
        form = product_ppmf_forms.ppmflow_product_update_form()
        if not form.validates(source=self.get_params()):
            return self.render('product_form.html', form=form)
        try:
            manager = ProductService(self.db, self.aes, operator=self.current_user)
            _params = dict(operator_name=self.current_user.username, operator_ip=self.current_user.ipaddr)
            ret = manager.update_ppmf(form.d, **_params)
            if ret:
                self.db.commit()
        except Exception as err:
            logger.exception(err)
            self.db.rollback()
            return self.render_error(msg=u'操作失败，请联系管理员：ERROR：%s' % repr(err))

        self.db.commit()
        self.redirect('/admin/product', permanent=False)