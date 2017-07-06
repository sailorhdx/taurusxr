#!/usr/bin/env python
# coding=utf-8
from taurusxradius.modules.dbservice.customer_add import CustomerAdd
from taurusxradius.modules.usrportal import order_forms
from taurusxradius.modules.usrportal.base import BaseHandler
from taurusxradius.taurusxlib.mail import send_mail
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.modules import models
from taurusxradius.taurusxlib.storage import Storage
from taurusxradius.taurusxlib.utils import QXToken


@permit.route('/usrportal/login')

class UsrPortalLoginHandler(BaseHandler):

    def get(self):
        if not self.current_user:
            form = order_forms.login_form()
            self.render('usrportal_login_form.html', form=form)
            return
        else:
            self.redirect('/usrportal/profile')
            return

    def post(self):

        form = order_forms.login_form()
        if not form.validates(source=self.get_params()):
            return self.render('usrportal_login_form.html', form=form)
        account_number = form.d.account_number
        password = form.d.password

        if not account_number:
            return self.render_json(code=1, msg=u'请填写用户名')
        if not password:
            return self.render_json(code=1, msg=u'请填写密码')


        account = self.db.query(models.TrAccount).get(account_number)
        if not account:
            return self.render_json(code=1, msg=u'账号不存在')
        if self.aes.decrypt(account.password) != password:
            return self.render_json(code=1, msg=u'密码错误')
        self.set_session_user(account.customer_id, account.account_number, self.request.remote_ip, utils.get_currtime(), account.status, account.expire_date, account.create_time)
        return self.render_json(code=0, msg='ok')

@permit.route('/usrportal/register')

class UsrPortalRegisterHandler(BaseHandler):

    def get(self):
        is_smsvcode = int(self.get_param_value('ssportal_smsvcode_required', 0))
        is_email = int(self.get_param_value('ssportal_email_required', 0))

        form = order_forms.register_form(is_smsvcode, is_email)
        self.render('usrportal_register_form.html', form=form)
        return
        #return self.render('usrportal_register.html', account_number=account_number)

    def post(self):

        is_smsvcode = int(self.get_param_value('ssportal_smsvcode_required', 0))
        is_email = int(self.get_param_value('ssportal_email_required', 0))

        form = order_forms.register_form(is_smsvcode, is_email)
        if not form.validates(source=self.get_params()):
            return self.render('usrportal_register_form.html', form=form)
        account_number = ''
        mobile = ''
        email = ''
        if is_smsvcode: #开启短信验证，使用手机号作为ID
            mobile = form.d.mobile
            account_number = mobile
        elif is_email: #开启邮件验证，使用邮箱地址作为ID
            email = form.d.email
            account_number = email
        else: # 否则用户自定义ID
            account_number = form.d.account_number
        password = form.d.password
        confirmpassword = form.d.confirmpassword

        if not account_number:
            errmsg = u'请填写用户名'
            if is_smsvcode:
                errmsg = u'请填写手机号码'
            elif is_email:
                errmsg = u'请填写邮箱地址'
            return self.render_json(code=1, msg=errmsg)
        if not password:
            return self.render_json(code=1, msg=u'请填写密码')
        if password != confirmpassword:
            return self.render_json(code=1, msg=u'两次密码输入不一致')

        account = self.db.query(models.TrAccount).get(account_number)
        if account_number and account:
            errmsg = u'用户帐号[%s]已经存在' % (account_number)
            if is_smsvcode:
                errmsg = u'手机号帐号[%s]已经存在' % (account_number)
            elif is_email:
                errmsg = u'邮箱帐号[%s]已经存在' % (account_number)
            return self.render_json(code=1, msg=errmsg)

        if is_smsvcode: #开启短信验证
            customer = self.db.query(models.TrCustomer).filter_by(mobile=mobile).scalar()
            if customer:
                return self.render_json(code=1, msg=u'手机号码[%s]已经存在于用户资料中，如果不是您正在使用的帐号，请联系管理员进行处理！' % (mobile))

            smsvcode = self.get_argument('vcode', '')
            if account_number and not smsvcode:
                return self.render_json(code=1, msg=u'验证码不能为空')
            logger.info('ssportal.sms.vcode = %s ' % self.cache.get('usrportal.sms.vcode.{}'.format(account_number)))
            if account_number and smsvcode and self.cache.get('usrportal.sms.vcode.{}'.format(account_number)) != smsvcode:
                return self.render_json(code=1, msg=u'验证码不匹配')

        elif is_email: #开启邮件验证
            customer = self.db.query(models.TrCustomer).filter_by(email=email).scalar()
            if customer:
                return self.render_json(code=1, msg=u'邮箱地址[%s]已经存在于用户资料中，如果不是您正在使用的帐号，请联系管理员进行处理！' % (email))

        # 添加帐号信息、用户信息
        cmanager = CustomerAdd(self.db, self.aes)
        ret = cmanager.add_account_from_portal(account_number=account_number, password=password, mobile=mobile, email=email, is_smsvcode=is_smsvcode, is_email=is_email)
        if not ret:
            return self.render_json(code=1, msg=cmanager.last_error)
        self.db.commit()

        if is_smsvcode :
            return self.render_json(code=0, msg=u'恭喜 %s ，手机帐号已成功注册！' % (str(account_number)))
        elif is_email: #开启邮件验证,发送激活验证邮件

            customer = self.db.query(models.TrCustomer).filter(
                models.TrCustomer.customer_id == models.TrAccount.customer_id,
                models.TrAccount.account_number == account_number).scalar()

            if not customer:
                return self.render_json(code=1, msg=u'用户[%s]添加异常' % (account_number))

            uuid = customer.active_code
            strToken = customer.token

            topic = 'TaurusXRadius注册激活邮件！'
            content = "尊敬的用户：" + str(account_number) + "\n\n\
            您好！\n\n\n\
            感谢您注册TaurusXRadius，请点击以下链接完成注册： \n\
            http://192.168.206.130:1829/usrportal/regconfirm?uuid=" + str(uuid) + "&token=" + str(strToken) + " \n\
            "

            sendEmail(self, email, topic, content)

            msgEmail = str(email[0:1] + 3 * '*' + email[email.find('@'):])
            return self.render_json(code=0, msg=u'恭喜 %s ，邮箱帐号已成功注册！我们已经将激活邮箱帐号的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，激活您的帐号。' % (msgEmail))
        else:
            return self.render_json(code=0, msg=u'恭喜 %s ，用户帐号已成功注册！' % (str(account_number)))

@permit.route('/usrportal/regconfirm')

class UsrPortalRegConfirmHandler(BaseHandler):

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
        customer.token = '' #激活成功清除Token信息，确保激活连接只能使用一次

        account = self.db.query(models.TrAccount).get(customer.customer_name)
        account.status = '1'
        self.db.commit()

        return self.render('info.html', msg=u'恭喜 %s ，帐号已成功激活！' % (str(customer.customer_name)))

@permit.route('/usrportal/forgot')

class UsrPortalForgotHandler(BaseHandler):

    def get(self):
        is_smsvcode = int(self.get_param_value('ssportal_smsvcode_required', 0))
        is_email = int(self.get_param_value('ssportal_email_required', 0))

        form = order_forms.forgot_form(is_smsvcode, is_email)
        if is_smsvcode or is_email:
            self.render('usrportal_forgot_form.html', form=form)
            return
        else:
            self.render('info.html', msg='未设置短信验证或邮件验证，不支持密码找回操作')
            return


    def post(self):
        is_smsvcode = int(self.get_param_value('ssportal_smsvcode_required', 0))
        is_email = int(self.get_param_value('ssportal_email_required', 0))

        form = order_forms.forgot_form(is_smsvcode, is_email)
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
                   http://192.168.206.130:1829/usrportal/resetpassword?uuid=" + str(uuid) + "&token=" + str(strToken) + " \n\n\
                   为了保证您帐号的安全性，该链接有效期为24小时，并且点击一次后将失效!\n\
                   "
            sendEmail(self, email, topic, content)
            msgEmail = str(email[0:1] + 3 * '*' + email[email.find('@'):])
            #return self.render('info.html', msg='我们已经将修改密码的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，重置您的密码。' % (msgEmail))
            return self.render_json(code=0, msg='我们已经将修改密码的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，重置您的密码。' % (msgEmail), is_email='1')

@permit.route('/usrportal/resetpassword')

class UsrPortalResetPasswordHandler(BaseHandler):

    def get(self):
        is_smsvcode = int(self.get_param_value('ssportal_smsvcode_required', 0))
        is_email = int(self.get_param_value('ssportal_email_required', 0))

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

        formResetpassword = order_forms.resetpassword_form(is_smsvcode=is_smsvcode,
                                                           is_email=is_email,
                                                           uuid=uuid,
                                                           token=strToken,
                                                           account_number=customer.customer_name,
                                                           mobile=customer.mobile,
                                                           email=customer.email)
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

@permit.route('/usrportal/logout')

class UsrPortalLogout2Handler(BaseHandler):

    def get(self):
        if not self.current_user:
            self.redirect('/usrportal/login')
            return
        self.clear_session()
        self.redirect('/usrportal/login', permanent=False)


def sendEmail(self, mail_to, topic, content):
    smtp_server = self.get_param_value('smtp_server', '127.0.0.1')
    smtp_port = self.get_param_value('smtp_port', 25)
    smtp_tls = int(self.get_param_value('smtp_tls', '0')) == 1
    smtp_from = self.get_param_value('smtp_from')
    smtp_user = self.get_param_value('smtp_user', None)
    smtp_pwd = self.get_param_value('smtp_pwd', None)

    ret = send_mail(server=smtp_server, port=smtp_port, user=smtp_user, password=smtp_pwd, from_addr=smtp_from,
                    mailto=mail_to, topic=topic, content=content, tls=smtp_tls)