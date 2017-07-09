#!/usr/bin/env python
# coding=utf-8
from taurusxradius.modules.settings import VcodeNotify
from taurusxradius.modules.usrportal.base import BaseHandler, authenticated
from taurusxradius.modules.usrportal import bind_forms
from taurusxradius.taurusxlib import logger, utils
from taurusxradius.taurusxlib.mail import send_mail, send_mail_self
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules import models
from taurusxradius.taurusxlib.utils import QXToken


@permit.route('/usrportal/bind/email')

class UsrPortalBindEmailHandler(BaseHandler):

    @authenticated
    def get(self):
        account_number = self.current_user.username
        account = self.db.query(models.TrAccount).get(account_number)
        if not account:
            return self.render('info.html', msg=u'账号不存在')
        customer = self.db.query(models.TrCustomer).get(account.customer_id)
        if not customer:
            return self.render('info.html', msg=u'用户数据不存在')

        form = bind_forms.bind_email_form(customer.email)
        self.render('profile_base_form.html', form=form)

    @authenticated
    def post(self):
        logger.info('smtp_tls = %s' % self.get_param_value('smtp_tls', '0'))
        form = bind_forms.bind_email_form()
        if not form.validates(source=self.get_params()):
            return self.render('profile_base_form.html', form=form)
        account_number = self.current_user.username
        account = self.db.query(models.TrAccount).get(account_number)
        if not account:
            return self.render('profile_base_form.html', form=form, msg=u'账号不存在')
        customer =  self.db.query(models.TrCustomer).get(account.customer_id)
        if not customer:
            return self.render('profile_base_form.html', form=form, msg=u'用户数据不存在')
        email = form.d.email

        if (email == customer.email and customer.email_active == 1):
            return self.render('profile_base_form.html', form=form, msg=u'您的帐号已经绑定此邮箱，无需重复绑定！')

        customer4check = self.db.query(models.TrCustomer).filter(models.TrCustomer.customer_id != customer.customer_id, models.TrCustomer.email_active == 1, models.TrCustomer.email == email).scalar()
        if customer4check:
            return self.render('profile_base_form.html', form=form,
                               msg=u'邮箱地址[%s]已经被其他帐号绑定，如果不是您正在使用的帐号，请联系管理员进行处理！' % (email))

        customer.email = email
        customer.email_active = '0'

        # 每次绑定生成新的UUID 和 TOKEN
        uuid = utils.get_uuid()
        token = QXToken('%s-%s-%s' % (customer.customer_id, customer.mobile, customer.email), uuid)
        strToken = token.generate_auth_token(expiration=86400)  # 密码重置Token有效期24小时，24*60*60秒

        customer.active_code = uuid
        customer.token = strToken

        self.db.commit()

        topic = 'TaurusXRadius绑定激活邮件！'
        content = "尊敬的用户：" + str(account_number) + "\n\n\
                    您好！\n\n\n\
                    感谢您使用TaurusXRadius，请点击以下链接完成绑定： \n\
                    http://" + self.request.host + "/usrportal/bind/email/confirm?uuid=" + str(uuid) + "&token=" + str(strToken) + " \n\
                    "

        send_mail_self(self, email, topic, content)
        msgEmail = str(email[0:1] + 3 * '*' + email[email.find('@'):])
        return self.render('profile_base_form.html', form=form, msg='我们已经将绑定邮箱的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，完成邮箱绑定操作。' % (msgEmail))


@permit.route('/usrportal/bind/email/confirm')

class UsrPortalBinMobileHandler(BaseHandler):

    def get(self):
        uUUid = self.get_argument('uuid', '')
        strToken = self.get_argument('token', '')

        customer = self.db.query(models.TrCustomer).filter(
            models.TrCustomer.active_code == uUUid).scalar()

        if not customer:
            return self.render('info.html', msg=u'请求数据异常，无法完成账户激活操作。')
        if customer.token != strToken:
            return self.render('info.html', msg=u'无效的Token信息，无法完成账户激活操作。')

        token = QXToken('%s-%s-%s' % (customer.customer_id, customer.mobile, customer.email), customer.active_code)
        ret = token.verify_auth_token(strToken)

        if not ret:
            # Token验证失败
            return self.render('info.html', msg=u'Token验证失败，无法完成账户激活操作。')

        customer.email_active = 1
        customer.active_code = utils.get_uuid()
        customer.token = ''  # 激活成功清除Token信息，确保激活连接只能使用一次

        account = self.db.query(models.TrAccount).get(customer.customer_name)
        account.status = '1'
        self.db.commit()

        return self.render('info.html', msg=u'恭喜 %s ，邮箱绑定成功！' % (str(customer.customer_name)))

@permit.route('/usrportal/bind/mobile')

class UsrPortalBinMobileHandler(BaseHandler):

    @authenticated
    def get(self):
        account_number = self.current_user.username
        account = self.db.query(models.TrAccount).get(account_number)
        if not account:
            return self.render('info.html', msg=u'账号不存在')
        customer = self.db.query(models.TrCustomer).get(account.customer_id)
        if not customer:
            return self.render('info.html', msg=u'用户数据不存在')

        form = bind_forms.bind_mobile_form(customer.mobile)
        self.render('profile_base_form.html', form=form)

    @authenticated
    def post(self):
        form = bind_forms.bind_mobile_form()
        if not form.validates(source=self.get_params()):
            return self.render('profile_base_form.html', form=form)
        account_number = self.current_user.username
        account = self.db.query(models.TrAccount).get(account_number)
        if not account:
            return self.render('profile_base_form.html', form=form, msg=u'账号不存在')
        customer =  self.db.query(models.TrCustomer).get(account.customer_id)
        if not customer:
            return self.render('profile_base_form.html', form=form, msg=u'用户数据不存在')
        mobile = form.d.mobile
        smsvcode = form.d.vcode

        if account_number and not mobile:
            return self.render('profile_base_form.html', form=form, msg=u'手机号不能为空')
        if account_number and not smsvcode:
            return self.render('profile_base_form.html', form=form, msg=u'验证码不能为空')
            #return self.render_json(code=1, msg=u'验证码不能为空')
        logger.info('usrportal.sms.vcode = %s ' % self.cache.get('usrportal.sms.vcode.{}'.format(mobile)))
        if account_number and smsvcode and self.cache.get('usrportal.sms.vcode.{}'.format(mobile)) != smsvcode:
            return self.render('profile_base_form.html', form=form, msg=u'验证码不匹配')
            #return self.render_json(code=1, msg=u'验证码不匹配')

        if (mobile == customer.mobile and customer.mobile_active == 1):
            return self.render('profile_base_form.html', form=form, msg=u'您的帐号已经绑定此手机号，无需重复绑定！')
        
        customer4check = self.db.query(models.TrCustomer).filter(models.TrCustomer.customer_id != customer.customer_id, models.TrCustomer.mobile_active == 1, models.TrCustomer.mobile == mobile).scalar()
        if customer4check:
            return self.render('profile_base_form.html', form=form,
                               msg=u'手机号[%s]已经被其他帐号绑定，如果不是您正在使用的帐号，请联系管理员进行处理！' % (mobile))

        customer.mobile = mobile
        customer.mobile_active = '1'
        self.db.commit()
        return self.render('profile_base_form.html', form=form, msg=u'手机绑定成功')