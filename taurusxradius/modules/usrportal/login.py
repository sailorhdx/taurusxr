#!/usr/bin/env python
# coding=utf-8
from taurusxradius.modules.dbservice.customer_add import CustomerAdd
from taurusxradius.modules.usrportal.base import BaseHandler
from taurusxradius.taurusxlib.mail import send_mail
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.modules import models
from taurusxradius.taurusxlib.utils import QXToken


@permit.route('/usrportal/login')

class UsrPortalLoginHandler(BaseHandler):

    def get(self):
        self.render('usrportal_login.html')

    def post(self):
        uUsername = self.get_argument('username', '')
        uPassword = self.get_argument('password', '')

        if not uUsername:
            return self.render_json(code=1, msg=u'请填写用户名')
        if not uPassword:
            return self.render_json(code=1, msg=u'请填写密码')


        account = self.db.query(models.TrAccount).get(uUsername)
        if not account:
            return self.render_json(code=1, msg=u'账号不存在')
        if self.aes.decrypt(account.password) != uPassword:
            return self.render_json(code=1, msg=u'密码错误')
        self.set_session_user(account.customer_id, account.account_number, self.request.remote_ip, utils.get_currtime(), account.status, account.expire_date, account.create_time)
        self.render_json(code=0, msg='ok')

@permit.route('/usrportal/register')

class UsrPortalRegisterHandler(BaseHandler):

    def get(self):
        self.render('usrportal_register.html')

    def post(self):
        uUsername = self.get_argument('username', '')
        uPassword = self.get_argument('password', '')
        uConfirmpassword = self.get_argument('confirmpassword', '')
        uEmail = self.get_argument('email', '')

        if not uUsername:
            return self.render_json(code=1, msg=u'请填写用户名')
        if not uPassword:
            return self.render_json(code=1, msg=u'请填写密码')
        if uPassword <> uConfirmpassword:
            return self.render_json(code=1, msg=u'两次密码输入不一致')
        if not uEmail:
            return self.render_json(code=1, msg=u'请填写电子邮件')
        account = self.db.query(models.TrAccount).get(uUsername)
        if account:
            return self.render_json(code=1, msg=u'用户名[%s]已经存在' % (uUsername))
        customer = self.db.query(models.TrCustomer).filter_by(email=uEmail).scalar()
        if customer:
            return self.render_json(code=1, msg=u'电子邮箱地址[%s]已经存在' % (uEmail))

        cmanager = CustomerAdd(self.db, self.aes)

        ret = cmanager.add_account_from_portal(uUsername, uPassword, uEmail)

        if not ret:
            return self.render_json(code=1, msg=cmanager.last_error)
        self.db.commit()

        customer = self.db.query(models.TrCustomer).filter_by(email=uEmail).scalar()
        uuid = customer.active_code
        token = QXToken('TaurusX', uuid)
        strToken = token.generate_auth_token()

        topic = 'TaurusXRadius注册激活邮件！'
        content = "尊敬的用户：" + str(uUsername) + "\n\n\
        您好！\n\n\n\
        感谢您注册TaurusXRadius，请点击以下链接完成注册： \n\
        http://192.168.206.130:1829/usrportal/regconfirm?uuid=" + str(uuid) + "&token=" + str(strToken) + " \n\
        "

        sendEmail(self, uEmail, topic, content)

        msgEmail = str(uEmail[0:1] + 3 * '*' + uEmail[uEmail.find('@'):])
        self.render_json(code=0, msg='我们已经将激活帐号的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，激活您的帐号。' % (msgEmail))

@permit.route('/usrportal/regconfirm')

class UsrPortalRegConfirmHandler(BaseHandler):

    def get(self):
        uUUid = self.get_argument('uuid', '')
        strToken = self.get_argument('token', '')

        token = QXToken('TaurusX', uUUid)
        ret = token.verify_auth_token(strToken)
        if not ret:
            # Token验证失败
            self.render('usrportal_regconfirm.html', msg='Token验证失败，无法更新密码。')

        customer = self.db.query(models.TrCustomer).filter(models.TrCustomer.active_code == uUUid).first()
        if not customer:
            self.render('usrportal_regconfirm.html', msg=u'账号不存在')
        customer.email_active = 1

        account = self.db.query(models.TrAccount).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id,
                                                         models.TrCustomer.active_code == uUUid).first()
        if not account:
            self.render('usrportal_regconfirm.html', msg=u'账号不存在')
        account.status = 1

        self.db.commit()

        self.render('usrportal_regconfirm.html', msg=u'恭喜 %s ，帐号已成功激活！' % (str(customer.customer_name)))

@permit.route('/usrportal/forgot')

class UsrPortalForgot2Handler(BaseHandler):

    def get(self):
        self.render('usrportal_forgot.html')

    def post(self):
        uUsername = self.get_argument('username', '')
        uEmail = self.get_argument('email', '')
        if not uUsername:
            return self.render_json(code=1, msg=u'请填写用户名')
        if not uEmail:
            return self.render_json(code=1, msg=u'请填写电子邮件')
        account = self.db.query(models.TrAccount).get(uUsername)
        if not account:
            return self.render_json(code=1, msg=u'用户名[%s]不存在' % (uUsername))
        if account.status == 0:
            return self.render_json(code=1, msg=u'用户名[%s]未激活' % (uUsername))
        customer = self.db.query(models.TrCustomer).get(account.customer_id)
        if not customer:
            return self.render_json(code=1, msg=u'用户名[%s]不存在' % (uUsername))
        elif customer.email != uEmail:
            return self.render_json(code=1, msg=u'电子邮箱地址[%s]不正确' % (uEmail))

        uuid= customer.active_code
        token = QXToken('TaurusX', uuid)
        strToken = token.generate_auth_token(expiration=86400) #密码重置Token有效期24小时，24*60*60秒

        topic = 'TaurusXRadius重置密码！'
        content = "尊敬的用户：" + str(uUsername) + "\n\n\
               您好！\n\n\n\
               请点击下面的链接修改用户 " + str(uUsername) + " 的密码：\n\
               http://192.168.206.130:1829/usrportal/resetpassword?uuid=" + str(uuid) + "&token=" + str(strToken) + " \n\n\
               为了保证您帐号的安全性，该链接有效期为24小时，并且点击一次后将失效!\n\
               "
        sendEmail(self, uEmail, topic, content)

        msgEmail = str(uEmail[0:1] + 3 * '*' + uEmail[uEmail.find('@'):])
        self.render_json(code=0, msg='我们已经将修改密码的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，重置您的密码。' % (msgEmail))

@permit.route('/usrportal/resetpassword')

class UsrPortalResetPasswordHandler(BaseHandler):

    def get(self):
        uUUid = self.get_argument('uuid', '')
        strToken = self.get_argument('token', '')
        token = QXToken('TaurusX', uUUid)
        ret = token.verify_auth_token(strToken)
        if not ret:
            # Token验证失败
            self.render('usrportal_resetpassword.html', msg='Token验证失败，无法更新密码。')
        self.render('usrportal_resetpassword.html', uuid=uUUid, token=strToken)

    def post(self):

        uUUid = self.get_argument('uuid', '')
        strToken = self.get_argument('token', '')
        uPassword = self.get_argument('password', '')
        uConfirmpassword = self.get_argument('confirmpassword', '')

        if not uUUid:
            return self.render_json(code=1, msg=u'用户激活码不能为空')
        if not strToken:
            return self.render_json(code=1, msg=u'用户受理令牌不能为空')
        if not uPassword:
            return self.render_json(code=1, msg=u'请填写密码')
        if uPassword <> uConfirmpassword:
            return self.render_json(code=1, msg=u'两次密码输入不一致')

        token = QXToken('TaurusX', uUUid)
        ret = token.verify_auth_token(strToken)
        if not ret:
            # Token验证失败
            self.render_json(code=1, msg=u'Token验证失败，无法更新密码。')

        account = self.db.query(models.TrAccount).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrCustomer.active_code == uUUid).first()
        if not account:
            self.render_json(code=1, msg=u'账号不存在')
        account.password = self.aes.encrypt(uPassword)
        self.db.commit()

        self.render_json(code=0, msg='恭喜 %s ，密码修改成功，请登录！' % (str(account.account_number)))

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

    logger.info('smtp_server = {0}'.format(smtp_server))
    logger.info('smtp_port = {0}'.format(smtp_port))
    logger.info('smtp_tls = {0}'.format(smtp_tls))
    logger.info('smtp_from = {0}'.format(smtp_from))
    logger.info('smtp_user = {0}'.format(smtp_user))
    logger.info('smtp_pwd = {0}'.format(smtp_pwd))
    logger.info('mail_to = {0}'.format(mail_to))

    ret = send_mail(server=smtp_server, port=smtp_port, user=smtp_user, password=smtp_pwd, from_addr=smtp_from,
                    mailto=mail_to, topic=topic, content=content, tls=smtp_tls)