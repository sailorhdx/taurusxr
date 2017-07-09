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
        is_smsvcode = int(self.get_param_value('usrportal_smsvcode_required', 0))
        is_email = int(self.get_param_value('usrportal_email_required', 0))

        form = forgot_forms.forgot_form(is_smsvcode, is_email)
        if is_smsvcode or is_email:
            self.render('usrportal_forgot_form.html', form=form)
            return
        else:
            self.render('info.html', msg='未设置短信验证或邮件验证，不支持密码找回操作')
            return


    def post(self):
        is_smsvcode = int(self.get_param_value('usrportal_smsvcode_required', 0))
        is_email = int(self.get_param_value('usrportal_email_required', 0))

        form = forgot_forms.forgot_form(is_smsvcode, is_email)
        if not form.validates(source=self.get_params()):
            return self.render('usrportal_forgot_form.html', form=form)
        account_number = ''
        mobile = ''
        email = ''
        if is_smsvcode:  # 开启短信验证，使用手机号作为ID
            mobile = form.d.mobile
            account_number = mobile
        elif is_email:  # 开启邮件验证，使用邮箱地址作为ID
            email = form.d.email
            account_number = email
        else:  # 否则用户自定义ID
            account_number = form.d.account_number

        if not account_number:
            errmsg = u'请填写用户名'
            if is_smsvcode:
                errmsg = u'请填写手机号码'
            elif is_email:
                errmsg = u'请填写邮箱地址'
            #return self.render('usrportal_forgot_form.html', form=form, msg=errmsg)
            return self.render_json(code=1, msg=errmsg)
        account = self.db.query(models.TrAccount).get(account_number)
        if not account:
            #return self.render('usrportal_forgot_form.html', form=form, msg=u'帐号[%s]不存在' % (account_number))
            return self.render_json(code=1, msg=u'帐号[%s]不存在' % (account_number))

        customer = self.db.query(models.TrCustomer).get(account.customer_id)
        if not customer:
            #return self.render('usrportal_forgot_form.html', form=form, msg=u'用户[%s]不存在' % (account_number))
            return self.render_json(code=1, msg=u'用户[%s]不存在' % (account_number))

        # 每次找回密码生成新的UUID 和 TOKEN
        uuid = utils.get_uuid()
        token = QXToken('%s-%s-%s' % (customer.customer_id, customer.mobile, customer.email), uuid)
        strToken = token.generate_auth_token(expiration=86400)  # 密码重置Token有效期24小时，24*60*60秒

        if is_smsvcode:
            smsvcode = form.d.vcode
            if account_number and not smsvcode:
                #return self.render('usrportal_forgot_form.html', form=form, msg=u'验证码不能为空')
                return self.render_json(code=1, msg=u'验证码不能为空')
            logger.info('usrportal.sms.vcode = %s ' % self.cache.get('usrportal.sms.vcode.{}'.format(account_number)))
            if account_number and smsvcode and self.cache.get('usrportal.sms.vcode.{}'.format(account_number)) != smsvcode:
                #return self.render('usrportal_forgot_form.html', form=form, msg=u'验证码不匹配')
                return self.render_json(code=1, msg=u'验证码不匹配')
        elif is_email:
            if customer.email != email:
                #return self.render('usrportal_forgot_form.html', form=form, msg=u'电子邮箱地址[%s]不正确' % (email))
                return self.render_json(code=1, msg=u'电子邮箱地址[%s]不正确' % (email))

        # 将重置密码使用的UUID和TOKEN数据存储到用户表中
        customer.active_code = uuid
        customer.token = strToken
        self.db.commit()

        if is_smsvcode:
            #formResetpassword = order_forms.resetpassword_form(is_smsvcode=is_smsvcode, uuid=uuid, token=strToken, account_number=account_number)
            #return self.render('usrportal_resetpassword_form.html', form=formResetpassword)
            return self.render_json(code=0, msg='手机号(%s)验证通过' % str(mobile), is_smsvcode='1', uuid=str(uuid), token=str(strToken))
        elif is_email:
            topic = 'TaurusXRadius重置密码！'
            content = "尊敬的用户：" + str(account_number) + "\n\n\
                   您好！\n\n\n\
                   请点击下面的链接修改用户 " + str(account_number) + " 的密码：\n\
                   http://" + self.request.host + "/usrportal/resetpassword?uuid=" + str(uuid) + "&token=" + str(strToken) + " \n\n\
                   为了保证您帐号的安全性，该链接有效期为24小时，并且点击一次后将失效!\n\
                   "
            send_mail_self(self, email, topic, content)
            msgEmail = str(email[0:1] + 3 * '*' + email[email.find('@'):])
            #return self.render('info.html', msg='我们已经将修改密码的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，重置您的密码。' % (msgEmail))
            return self.render_json(code=0, msg='我们已经将修改密码的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，重置您的密码。' % (msgEmail), is_email='1')