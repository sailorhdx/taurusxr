#!/usr/bin/env python
# coding=utf-8
import datetime

from taurusxradius.modules.dbservice.customer_add import CustomerAdd
from taurusxradius.modules.usrportal import register_forms
from taurusxradius.modules.usrportal.base import BaseHandler
from taurusxradius.taurusxlib.mail import send_mail_self
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.modules import models
from taurusxradius.taurusxlib.utils import QXToken

@permit.route('/usrportal/register')
class UsrPortalRegisterHandler(BaseHandler):

    def get(self):
        is_smsvcode = int(self.get_param_value('usrportal_smsvcode_required', 0))
        is_email = int(self.get_param_value('usrportal_email_required', 0))

        form = register_forms.register_form(is_smsvcode, is_email)
        self.render('usrportal_register_form.html', form=form)
        return
        #return self.render('usrportal_register.html', account_number=account_number)

    def post(self):

        is_smsvcode = int(self.get_param_value('usrportal_smsvcode_required', 0))
        is_email = int(self.get_param_value('usrportal_email_required', 0))

        form = register_forms.register_form(is_smsvcode, is_email)
        _validates, _msg = form.validatesjson(source=self.get_params())
        if not _validates:
            return self.render_json(code=1, json=1, msg=_msg)

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
                return self.render_json(code=1, msg=u'手机号[%s]被其他账号绑定，如果不是您正在使用的帐号，请联系管理员进行处理！' % (mobile))

            smsvcode = self.get_argument('vcode', '')
            if account_number and not smsvcode:
                return self.render_json(code=1, msg=u'验证码不能为空')
            logger.info('usrportal.sms.vcode = %s ' % self.cache.get('usrportal.sms.vcode.{}'.format(account_number)))
            if account_number and smsvcode and self.cache.get('usrportal.sms.vcode.{}'.format(account_number)) != smsvcode:
                return self.render_json(code=1, msg=u'验证码不匹配')

        elif is_email: #开启邮件验证
            customer = self.db.query(models.TrCustomer).filter_by(email=email).scalar()
            if customer:
                return self.render_json(code=1, msg=u'邮箱[%s]被其他账号绑定，如果不是您正在使用的帐号，请联系管理员进行处理！' % (email))

        # 添加帐号信息、用户信息
        cmanager = CustomerAdd(self.db, self.aes)
        product_id = self.get_param_value('default_product_policy', 'HOLD-000000-NONE')  # 从参数的默认资费策略中读取默认产品ID

        form = register_forms.register_customer_open_form()
        form.node_id.set_value('1')
        form.area_id.set_value('1')
        form.realname.set_value(account_number)
        form.mobile.set_value(mobile)
        form.email.set_value(email)
        form.account_number.set_value(account_number)
        form.password.set_value(password)
        form.product_id.set_value(product_id)
        _fee_value, _expire_date = self.order_calc(product_id)
        form.fee_value.set_value(_fee_value)
        if _expire_date == datetime.datetime.now().strftime('%Y-%m-%d'):
            """如果有效期与当前日期相等，则将有效期减一天，使帐号立即失效"""
            _expire_date = datetime.datetime.strptime(_expire_date, '%Y-%m-%d') - datetime.timedelta(days=1)
            _expire_date = _expire_date.strftime('%Y-%m-%d')
        form.expire_date.set_value(_expire_date)

        form.billing_type.set_value('1')

        _params = dict(operator_name=account_number, operator_ip=self.request.remote_ip)
        ret = cmanager.add(form.d, **_params)
        if not ret:
            return self.render_json(code=1, msg=cmanager.last_error)
        self.db.commit()

        account = self.db.query(models.TrAccount).get(account_number)
        if not account:
            return self.render_json(code=1, msg=u'帐号[%s]添加异常' % (account_number))
        customer = self.db.query(models.TrCustomer).get(account.customer_id)
        if not customer:
            return self.render_json(code=1, msg=u'用户[%s]添加异常' % (account_number))

        if is_smsvcode :
            customer.mobile_active = 1
            self.db.commit()
            return self.render_json(code=0, msg=u'恭喜 %s ，手机帐号已成功注册！' % (str(account_number)))
        elif is_email: #开启邮件验证,发送激活验证邮件

            uuid = utils.get_uuid()

            token = QXToken('%s-%s-%s' % (customer.customer_id, customer.mobile, customer.email), uuid)
            strToken = token.generate_auth_token()

            customer.active_code = uuid
            customer.token = strToken
            self.db.commit()

            topic = 'TaurusXRadius注册激活邮件！'
            content = "尊敬的用户：" + str(account_number) + "\n\n\
            您好！\n\n\n\
            感谢您注册TaurusXRadius，请点击以下链接完成注册： \n\
            http://" + self.request.host + "/usrportal/register/confirm?uuid=" + str(uuid) + "&token=" + str(strToken) + " \n\
            "

            send_mail_self(self, email, topic, content)

            msgEmail = str(email[0:1] + 3 * '*' + email[email.find('@'):])
            return self.render_json(code=0, msg=u'我们已经将激活邮箱帐号的链接发送到你的邮箱(%s)，请前往您的邮箱点击链接，激活您的帐号。' % (msgEmail))
        else:
            return self.render_json(code=0, msg=u'恭喜 %s ，用户帐号已成功注册！' % (str(account_number)))

@permit.route('/usrportal/register/confirm')

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