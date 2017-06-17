#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils, logger
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules import settings
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.wlan import domain_form
from toughradius.common import tools
import json

@permit.suproute('/admin/wlan/domain/ap/add', u'新增 AP 设备', settings.ResWlan, order=1.0005)

class DomainApAddHandler(BaseHandler):

    @authenticated
    def post(self):
        try:
            form = domain_form.domain_ap_add_form()
            if not form.validates(source=self.get_params()):
                return self.render_json(code=1, msg=form.errors)
            domain_ap = self.db.query(models.TrDomainAp).filter_by(domain_code=form.d.domain_code, guid=form.d.guid).first()
            if domain_ap:
                return self.render_json(code=1, msg=u'ap 已经存在')
            domain_ap = models.TrDomainAp()
            domain_ap.id = tools.gen_num_id(16)
            domain_ap.domain_code = form.d.domain_code
            domain_ap.guid = form.d.guid
            domain_ap.ssid = form.d.ssid
            domain_ap.ap_desc = form.d.ap_desc
            domain_ap.sync_ver = tools.gen_sync_ver()
            self.db.add(domain_ap)
            self.db.commit()
            return self.render_json(msg=u'保存成功')
        except Exception as err:
            logger.exception(err)
            return self.render_json(code=1, msg=u'保存失败，请联系客服 %s' % repr(err))


@permit.suproute('/admin/wlan/domain/ap/delete', u'AP 设备删除', settings.ResWlan, order=1.0007)

class DomainApDeleteHandler(BaseHandler):

    @authenticated
    def get(self):
        ap_id = self.get_argument('ap_id')
        ap = self.db.query(models.TrDomainAp).get(ap_id)
        if not ap:
            return self.render_error(msg=u'ap不存在')
        domain_code = ap.domain_code
        self.db.query(models.TrDomainAp).filter_by(id=ap_id).delete()
        self.db.commit()
        domain_id = self.db.query(models.TrDomain.id).filter_by(domain_code=domain_code).scalar()
        self.redirect('/admin/wlan/domain/detail?domain_id=%s&active=domainaps' % domain_id)