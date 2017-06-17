#!/usr/bin/env python
# coding=utf-8
import datetime
import time
import json
import decimal
import string
import os
from hashlib import md5
from toughradius.toughlib import utils, logger
from toughradius.modules.ssportal.base import BaseHandler, authenticated
from toughradius.modules.ssportal import order_forms
from toughradius.modules.ssportal import alipayment_new
from toughradius.toughlib.permit import permit
from toughradius.toughlib.storage import Storage
from toughradius.modules import models
from toughradius.common import tools
from toughradius.modules.dbservice.account_charge import AccountCharge
if os.environ.get('LICENSE_TYPE') != 'community':

    @permit.route('/ssportal/product/vcardcharge')

    class SSportalVcardChargeOrderHandler(BaseHandler):
        """ 发起充值卡流量充值
        """

        @authenticated
        def get(self):
            account_number = self.current_user.username
            account = self.db.query(models.TrAccount).get(account_number)
            product_id = account.product_id
            product = self.db.query(models.TrProduct).get(product_id)
            if not product:
                return self.render_alert(u'错误提示', u'套餐不存在')
            form = order_forms.vcard_charge_form()
            form.account_number.set_value(account_number)
            form.product_id.set_value(product_id)
            form.product_name.set_value(product.product_name)
            self.render('vcard_charge_modal_form.html', form=form)

        def post(self):
            form = order_forms.vcard_charge_form()
            if not form.validates(source=self.get_params()):
                return self.render_json(code=1, msg=form.errors)
            account = self.db.query(models.TrAccount).get(form.d.account_number)
            if not account:
                return self.render_json(code=1, msg=u'账号不存在')
            try:
                order_id = utils.gen_order_id()
                formdata = Storage(form.d)
                formdata['order_id'] = order_id
                formdata['product_id'] = account.product_id
                formdata['fee_value'] = '0.00'
                formdata['accept_source'] = 'ssportal'
                formdata['operate_desc'] = u'用户自助充值卡充值'
                formdata['vcard_code'] = form.d.vcard_code
                formdata['vcard_pwd'] = form.d.vcard_pwd
                manager = AccountCharge(self.db, self.aes)
                ret = manager.charge(formdata)
                if ret:
                    logger.info(u'充值卡充值成功')
                    self.render_json(code=0, msg=u'充值卡充值成功')
                else:
                    return self.render_json(code=1, msg=u'充值卡订单处理失败 %s' % manager.last_error)
            except Exception as err:
                logger.exception(err)
                return self.render_json(code=1, msg=u'无效的订单')