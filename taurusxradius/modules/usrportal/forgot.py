#!/usr/bin/env python
# coding=utf-8

from taurusxradius.modules.usrportal import forgot_forms
from taurusxradius.modules.usrportal.base import BaseHandler
from taurusxradius.taurusxlib.mail import send_mail_self
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.modules import models
from taurusxradius.taurusxlib.utils import QXToken

@permit.route('/usrportal/forgot/mobile')

class UsrPortalForgotMobileHandler(BaseHandler):

    def get(self):
        form = forgot_forms.forgot_mobile_form()
        self.render('usrportal_forgot_form.html', form=form)
        return

    def post(self):

        form = forgot_forms.forgot_mobile_form()
        if not form.validates(source=self.get_params()):
            return self.render('usrportal_forgot_form.html', form=form)
        mobile = form.d.mobile
        if not mobile:
            #return self.render('usrportal_forgot_form.html', form=form, msg=errmsg)
            return self.render_json(code=1, msg=u'请填写手机号码')

        customer = self.db.query(models.TrCustomer).filter(
            models.TrCustomer.mobile_active == 1, models.TrCustomer.mobile == mobile).scalar()
        if not customer:
            #return self.render('usrportal_forgot_form.html', form=form, msg=u'用户[%s]不存在' % (account_number))
            return self.render_json(code=1, msg=u'手机号[%s]未被用户绑定' % (mobile))

        # 每次找回密码生成新的UUID 和 TOKEN
        uuid = utils.get_uuid()
        token = QXToken('%s-%s-%s' % (customer.customer_id, customer.mobile, customer.email), uuid)
        strToken = token.generate_auth_token(expiration=86400)  # 密码重置Token有效期24小时，24*60*60秒

        smsvcode = form.d.vcode
        if customer and not smsvcode:
            # return self.render('usrportal_forgot_form.html', form=form, msg=u'验证码不能为空')
            return self.render_json(code=1, msg=u'验证码不能为空')
        logger.info('usrportal.sms.vcode = %s ' % self.cache.get('usrportal.sms.vcode.{}'.format(mobile)))
        if customer and smsvcode and self.cache.get('usrportal.sms.vcode.{}'.format(mobile)) != smsvcode:
            # return self.render('usrportal_forgot_form.html', form=form, msg=u'验证码不匹配')
            return self.render_json(code=1, msg=u'验证码不匹配')

        # 将重置密码使用的UUID和TOKEN数据存储到用户表中
        customer.active_code = uuid
        customer.token = strToken
        self.db.commit()

        #formResetpassword = order_forms.resetpassword_form(is_smsvcode=is_smsvcode, uuid=uuid, token=strToken, account_number=account_number)
        #return self.render('usrportal_resetpassword_form.html', form=formResetpassword)
        return self.render_json(code=0, msg='手机号(%s)验证通过' % str(mobile), is_smsvcode='1', uuid=str(uuid), token=str(strToken))

@permit.route('/usrportal/forgot/email')

class UsrPortalForgotEmailHandler(BaseHandler):

    def get(self):
        form = forgot_forms.forgot_email_form()
        self.render('usrportal_forgot_form.html', form=form)
        return

    def post(self):

        form = forgot_forms.forgot_email_form()
        if not form.validates(source=self.get_params()):
            return self.render('usrportal_forgot_form.html', form=form)

        email = form.d.email
        if not email:
            #return self.render('usrportal_forgot_form.html', form=form, msg=errmsg)
            return self.render_json(code=1, msg=u'请填写邮箱地址')

        customer = self.db.query(models.TrCustomer).filter(
            models.TrCustomer.email_active == 1, models.TrCustomer.email == email).scalar()
        if not customer:
            #return self.render('usrportal_forgot_form.html', form=form, msg=u'用户[%s]不存在' % (account_number))
            return self.render_json(code=1, msg=u'邮箱[%s]未被用户绑定' % (email))

        # 每次找回密码生成新的UUID 和 TOKEN
        uuid = utils.get_uuid()
        token = QXToken('%s-%s-%s' % (customer.customer_id, customer.mobile, customer.email), uuid)
        strToken = token.generate_auth_token(expiration=86400)  # 密码重置Token有效期24小时，24*60*60秒

        # 将重置密码使用的UUID和TOKEN数据存储到用户表中
        customer.active_code = uuid
        customer.token = strToken
        self.db.commit()

        topic = 'TaurusXRadius重置密码！'
        content = "尊敬的用户：" + str(customer.customer_name) + "\n\n\
               您好！\n\n\n\
               请点击下面的链接修改用户 " + str(customer.customer_name) + " 的密码：\n\
               http://" + self.request.host + "/usrportal/resetpassword?uuid=" + str(uuid) + "&token=" + str(strToken) + " \n\n\
               为了保证您帐号的安全性，该链接有效期为24小时，并且点击一次后将失效!\n\
               "
        send_mail_self(self, email, topic, content)
        msgEmail = str(email[0:1] + 3 * '*' + email[email.find('@'):])
        #return self.render('info.html', msg='我们已经将修改密码的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，重置您的密码。' % (msgEmail))
        return self.render_json(code=0, msg='我们已经将修改密码的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，重置您的密码。' % (msgEmail), is_email='1')

@permit.route('/usrportal/forgot')

class UsrPortalForgotHandler(BaseHandler):

    def get(self):
        return self.render('usrportal_forgot.html')