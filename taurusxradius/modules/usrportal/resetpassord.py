#!/usr/bin/env python
# coding=utf-8

from taurusxradius.modules.usrportal import order_forms, resetpassword_forms
from taurusxradius.modules.usrportal.base import BaseHandler
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.modules import models
from taurusxradius.taurusxlib.utils import QXToken

@permit.route('/usrportal/resetpassword')

class UsrPortalResetPasswordHandler(BaseHandler):

    def get(self):
        uuid = self.get_argument('uuid', '')
        strToken = self.get_argument('token', '')

        customer = self.db.query(models.TrCustomer).filter(
            models.TrCustomer.active_code == uuid).scalar()

        if not customer:
            return self.render('info.html', msg=u'请求数据异常，无法更新密码。')
        if customer.token != strToken:
            return self.render('info.html', msg=u'无效的Token信息，无法更新密码。')

        token = QXToken('%s-%s-%s' % (customer.customer_id, customer.mobile, customer.email), customer.active_code)
        ret = token.verify_auth_token(strToken)
        if not ret:
            # Token验证失败
            return self.render('info.html', msg=u'Token验证失败，无法更新密码。')

        formResetpassword = resetpassword_forms.resetpassword_form(uuid=uuid,
                                                           token=strToken)
        return self.render('usrportal_resetpassword_form.html', form=formResetpassword)
        #return self.render('usrportal_resetpassword_form.html', uuid=uUUid, token=strToken)

    def post(self):

        uUUid = self.get_argument('uuid', '')
        strToken = self.get_argument('token', '')
        uPassword = self.get_argument('password', '')
        uConfirmpassword = self.get_argument('confirmpassword', '')

        if not uUUid:
            return self.render_json(code=1, msg=u'用户激活码不能为空')
        if not strToken:
            return self.render_json(code=1, msg=u'Token信息不能为空')
        if not uPassword:
            return self.render_json(code=1, msg=u'请填写密码')
        if uPassword <> uConfirmpassword:
            return self.render_json(code=1, msg=u'两次密码输入不一致')

        customer = self.db.query(models.TrCustomer).filter(
            models.TrCustomer.active_code == uUUid).scalar()

        if not customer:
            return self.render_json(code=1, msg=u'请求数据异常，无法更新密码。')
        if customer.token != strToken:
            return self.render_json(code=1, msg=u'无效的Token信息，无法更新密码。')

        token = QXToken('%s-%s-%s' % (customer.customer_id, customer.mobile, customer.email), customer.active_code)
        ret = token.verify_auth_token(strToken)
        if not ret:
            # Token验证失败
            return self.render_json(code=1, msg=u'Token验证失败，无法更新密码。')

        customer.active_code = utils.get_uuid()
        customer.token = '' #重置成功清除Token信息，确保重置密码连接只能使用一次

        account = self.db.query(models.TrAccount).get(customer.customer_name)
        if not account:
            return self.render_json(code=1, msg=u'账号不存在')
        account.password = self.aes.encrypt(uPassword)

        self.db.commit()

        return self.render_json(code=0, msg='恭喜 %s ，密码修改成功，请登录！' % (str(account.account_number)))
