#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.toughlib import logger
from toughradius.toughlib import utils
from toughradius.toughlib.permit import permit
from toughradius.modules.mps.base import BaseHandler
from twisted.internet import defer
from toughradius.modules import models
from urllib import urlencode
from toughradius.common import tools
import base64

@permit.route('/mps/userinfo')

class MpsUserbindHandler(BaseHandler):

    def get(self):
        openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
        if not openid:
            cbk_param = urlencode({'cbk': '/mps/userinfo'})
            return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
        customer = self.db.query(models.TrCustomer).filter_by(wechat_oid=openid).first()
        if not customer:
            return self.redirect('/mps/userbind', permanent=False)
        user = self.db.query(models.TrCustomer.realname, models.TrCustomer.wechat_oid, models.TrCustomer.mobile, models.TrCustomer.email, models.TrAccount.customer_id, models.TrAccount.account_number, models.TrAccount.expire_date, models.TrAccount.balance, models.TrAccount.time_length, models.TrAccount.flow_length, models.TrAccount.user_concur_number, models.TrAccount.status, models.TrAccount.mac_addr, models.TrAccount.ip_address, models.TrAccount.ip_address, models.TrAccount.install_address, models.TrAccount.last_pause, models.TrAccount.create_time, models.TrProduct.product_name, models.TrProduct.product_policy).filter(models.TrProduct.id == models.TrAccount.product_id, models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrCustomer.wechat_oid == openid).first()
        if not user:
            return self.render('error.html', msg=u'用户不存在')
        self.render('userinfo.html', user=user)