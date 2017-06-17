#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils, logger
from toughradius.toughlib import db_cache
from toughradius.toughlib import dispatch
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules import settings
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.wlan import domain_form
from toughradius.common import tools
import json

@permit.suproute('/admin/wlan/domain', u'认证域管理', settings.ResWlan, order=1.0, is_menu=True)

class DomainHandler(BaseHandler):

    @authenticated
    def get(self):
        domains = self.db.query(models.TrDomain)
        self.render('domain_list.html', domains=domains)


@permit.suproute('/admin/wlan/domain/detail', u'认证域详情', settings.ResWlan, order=1.0001)

class DomainDetailHandler(BaseHandler):

    @authenticated
    def get(self):
        active = self.get_argument('active', 'domainattrs')
        domain_id = self.get_argument('domain_id')
        domain = self.db.query(models.TrDomain).filter_by(id=domain_id).first()
        products = [ (p.id, p.product_name) for p in self.get_opr_products() ]
        attrs = self.db.query(models.TrDomainAttr).filter_by(domain_code=domain.domain_code)
        aps = self.db.query(models.TrDomainAp).filter_by(domain_code=domain.domain_code)
        apform = domain_form.domain_ap_add_form()
        apform.guid.set_value(tools.gen_num_id(16))
        apform.domain_code.set_value(domain.domain_code)
        attrsform = domain_form.domain_attr_form(products=products)
        attrmap = {}
        for p in self.db.query(models.TrDomainAttr).filter_by(domain_code=domain.domain_code):
            attrmap[p.attr_name] = p.attr_value

        attrsform.fill(attrmap)
        attrsform.domain_code.set_value(domain.domain_code)
        attrsform.tpl_name.set_value(domain.tpl_name)
        self.render('domain_detail.html', active=active, domain_id=domain_id, domain=domain, attrs=attrs, aps=aps, apform=apform, attrsform=attrsform)


@permit.suproute('/admin/wlan/domain/add', u'认证域信息创建', settings.ResWlan, order=1.0002)

class AddHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('base_form.html', form=domain_form.domain_add_vform())

    @authenticated
    def post(self):
        form = domain_form.domain_add_vform()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        if self.db.query(models.TrDomain.id).filter_by(domain_code=form.d.domain_code).count() > 0:
            return self.render('base_form.html', form=form, msg=u'域已经存在')
        domain = models.TrDomain()
        domain.id = tools.gen_num_id(16)
        domain.tpl_name = form.d.tpl_name
        domain.domain_code = form.d.domain_code
        domain.domain_desc = form.d.domain_desc
        domain.sync_ver = tools.gen_sync_ver()
        self.db.add(domain)
        self.add_oplog(u'新增域信息:%s' % form.d.domain_code)
        self.db.commit()
        self.redirect('/admin/wlan/domain', permanent=False)


@permit.suproute('/admin/wlan/domain/update', u'认证域修改', settings.ResWlan, order=1.0003)

class UpdateHandler(BaseHandler):

    @authenticated
    def get(self):
        domain_id = self.get_argument('domain_id')
        form = domain_form.domain_update_vform()
        form.fill(self.db.query(models.TrDomain).get(domain_id))
        return self.render('base_form.html', form=form)

    def post(self):
        form = domain_form.domain_update_vform()
        if not form.validates(source=self.get_params()):
            return self.render('base_form.html', form=form)
        domain = self.db.query(models.TrDomain).get(form.d.id)
        domain.tpl_name = form.d.tpl_name
        domain.domain_desc = form.d.domain_desc
        domain.sync_ver = tools.gen_sync_ver()
        self.add_oplog(u'修改域信息:%s' % domain.domain_code)
        self.db.commit()
        self.redirect('/admin/wlan/domain', permanent=False)


@permit.suproute('/admin/wlan/domain/delete', u'认证域删除', settings.ResWlan, order=1.0004)

class DeleteHandler(BaseHandler):

    @authenticated
    def post(self):
        domain_id = self.get_argument('domain_id')
        domain = self.db.query(models.TrDomain).get(domain_id)
        if not domain:
            return self.render_json(code=0, msg=u'要删除的域不存在!')
        self.db.query(models.TrDomainAttr).filter_by(domain_code=domain.domain_code).delete()
        self.db.query(models.TrDomainAp).filter_by(domain_code=domain.domain_code).delete()
        self.db.query(models.TrDomain).filter_by(id=domain_id).delete()
        self.add_oplog(u'删除域信息:%s' % domain_id)
        self.db.commit()
        return self.render_json(code=0, msg=u'删除域成功!')


@permit.suproute('/admin/wlan/domain/attr/update', u'认证域属性新增', settings.ResWlan, order=2.0001)

class DomainAttrUpdateHandler(BaseHandler):

    @authenticated
    def post(self):
        params = self.get_params()
        domain_code = params.pop('domain_code')
        domain = self.db.query(models.TrDomain).filter_by(domain_code=domain_code).first()
        for attr_name in params:
            if attr_name in ('active', 'submit', 'domain_code', 'tpl_name'):
                continue
            domain_attr = self.db.query(models.TrDomainAttr).filter_by(domain_code=domain_code, attr_name=attr_name).first()
            if not domain_attr:
                domain_attr = models.TrDomainAttr()
                domain_attr.id = tools.gen_num_id(16)
                domain_attr.domain_code = domain_code
                domain_attr.attr_name = attr_name
                domain_attr.attr_value = self.get_argument(attr_name)
                domain_attr.attr_desc = ''
                domain_attr.sync_ver = tools.gen_sync_ver()
                self.db.add(domain_attr)
            else:
                domain_attr.attr_value = self.get_argument(attr_name)
            dispatch.pub(db_cache.CACHE_SET_EVENT, settings.wlanattr_cache_key(domain_attr.attr_name), domain_attr.attr_value, 600)

        self.add_oplog(u'操作员(%s)修改wlan参数' % self.current_user.username)
        self.db.commit()
        self.redirect('/admin/wlan/domain/detail?domain_id=%s' % domain.id)