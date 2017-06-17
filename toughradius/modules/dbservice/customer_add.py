#!/usr/bin/env python
# coding=utf-8
import traceback
import datetime
import string
import random
import json
from toughradius.modules.settings import *
from toughradius.common import tools
from hashlib import md5
from toughradius.modules import models
from toughradius.toughlib import utils, dispatch, logger
from toughradius.modules.events.settings import ACCOUNT_OPEN_EVENT
from toughradius.modules.events.settings import ISSUES_ASSIGN_EVENT
from toughradius.modules.dbservice import BaseService
from toughradius.modules.dbservice import logparams
from toughradius.common import tools
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.storage import Storage
from toughradius.modules.events import settings as evset

class CustomerAdd(BaseService):

    def add_account_fixdflows(self, account_number, flows):
        attr = models.TrAccountAttr()
        attr.id = utils.get_uuid()
        attr.account_number = account_number
        attr.attr_type = 0
        attr.attr_name = 'fixd_flows'
        attr.attr_value = flows
        attr.attr_desc = '用户固定流量'
        attr.sync_ver = tools.gen_sync_ver()
        self.db.add(attr)

    def update_routeros_sync_event(self, name, pwd, profile, node_id):
        dispatch.pub(evset.ROSSYNC_SET_PPPOE_USER, name, pwd, profile, node_id=node_id, async=True)
        dispatch.pub(evset.ROSSYNC_SET_HOTSPOT_USER, name, pwd, profile, node_id=node_id, async=True)

    def check_data(self, formdata):
        """
        用户开户数据校验
        """
        max_giftdays = self.db.query(models.TrProductAttr.attr_value).filter_by(product_id=formdata.product_id, attr_name='max_giftdays').scalar() or 0
        if int(max_giftdays) < int(formdata.get('giftdays', 0)):
            self.last_error = u'最大赠送天数不能超过%s天' % max_giftdays
            return False
        max_giftflows = self.db.query(models.TrProductAttr.attr_value).filter_by(product_id=formdata.product_id, attr_name='max_giftflows').scalar() or 0
        if float(max_giftflows) < float(formdata.get('giftflows', 0)):
            self.last_error = u'最大赠送流量不能超过%sG' % max_giftflows
            return False
        node = self.db.query(models.TrNode).get(formdata.node_id)
        if not node:
            self.last_error = u'区域节点不存在'
            return False
        account_count = self.db.query(models.TrAccount).filter_by(account_number=formdata.account_number).count()
        if account_count > 0:
            self.last_error = u'账号%s已经存在' % formdata.account_number
            return False
        _ip_address = formdata.get('ip_address')
        if _ip_address and self.db.query(models.TrAccount).filter_by(ip_address=_ip_address).count() > 0:
            self.last_error = u'ip%s已经被使用' % utils.safestr(_ip_address)
            return False
        if self.db.query(models.TrCustomer).filter_by(customer_name=formdata.account_number).count() > 0:
            if account_count == 0:
                self.db.query(models.TrCustomer).filter_by(customer_name=formdata.account_number).delete()
            else:
                self.last_error = u'用户名%s已经存在' % formdata.account_number
                return False
        return True

    def check_vcard(self, vcard, vcard_pwd, product):
        if not vcard:
            self.last_error = u'充值卡不存在'
            return False
        if vcard.status == 0:
            self.last_error = u'充值卡未激活'
            return False
        if vcard.status == 2:
            self.last_error = u'充值卡已使用'
            return False
        if utils.is_expire(vcard.expire_date):
            self.last_error = u'充值卡已过期'
            return False
        if vcard.card_type not in 'product':
            self.last_error = u'充值卡不是套餐卡'
            return False
        if self.aes.decrypt(vcard.card_pwd) != vcard_pwd:
            self.last_error = u'充值卡密码错误'
            return False
        if product.product_policy not in (BOMonth,
         BOFlows,
         BOTimes,
         BODay):
            self.last_error = u'当前资费不支持此充值卡'
            return False
        pattr = self.db.query(models.TrProductAttr).filter_by(product_id=product.id, attr_name='product_tag', attr_value=vcard.product_tag).first()
        if not pattr:
            self.last_error = u'当前资费不支持此充值卡'
            return False
        return True

    def warp_account_data(self, account, status = 1):
        data = dict(product_id=account.product_id, status=status, balance=account.balance, time_length=account.time_length, flow_length=account.flow_length, expire_date=account.expire_date)
        return json.dumps(data, ensure_ascii=False)

    @logparams
    def add(self, formdata, **kwargs):
        """用户开户

        :param formdata:   用户开户参数表
        :type formdata:    dict

        formdata params:

        :param account_number:   用户账号
        :type account_number:    string
        :param billing_type:   计费模式，0 首次上线计费 1 立即计费
        :type billing_type:    int
        :param customer_id:   客户ID，16-32位字符串（可选）
        :type customer_id:    string
        :param order_id:   交易ID，16-32位字符串（可选）
        :type order_id:    string
        :param product_id:   订购资费ID
        :type product_id:    string
        :param node_id:   用户区域ID
        :type node_id:    string
        :param area_id:   用户社区ID（可选）
        :type area_id:    string
        :param agency_id:   代理商ID（可选）
        :type agency_id:    string
        :param realname:   用户姓名
        :type realname:    string
        :param password:   用户账号密码
        :type password:    string
        :param ip_address:   用户IP地址
        :type ip_address:    string
        :param idcard:   用户身份证号码（可选）
        :type idcard:    string
        :param email:   用户电子邮箱（可选）
        :type email:    string
        :param mobile:   用户手机号码（可选）
        :type mobile:    string
        :param address:   用户地址（可选）
        :type address:    string
        :param customer_desc:   用户描述备注（可选）
        :type customer_desc:    string
        :param accept_source:   用户受理来源（可选）
        :type accept_source:    string
        :param expire_date:   用户到期时间 yyyy-mm-dd
        :type expire_date:    string
        :param months:   用户订购月数，预付费包月有效
        :type days:    int
        :param days:    用户订购天数，预付费包日有效
        :type months:    int
        :param fee_value:   交易费用 x.xx 元
        :type fee_value:    string
        :param giftflows:   赠送流量 x.xx GB
        :type giftflows:    string
        :param giftdays:   赠送天数
        :type giftdays:    int
        :param charge_code:   收费项目编码
        :type charge_code:    string
        :param builder_name:   服务人员名
        :type builder_name:    string
        :param vcard_code:   充值卡
        :type vcard_code:    string
        :param vcard_pwd:   充值卡密码
        :type vcard_pwd:    string
        """
        try:
            account_number = self.parse_arg(formdata, 'account_number', rule=rules.not_null)
            account_number = account_number.strip()
            formdata['account_number'] = account_number
            billing_type = int(formdata.get('billing_type', 1))
            pay_status = int(formdata.get('pay_status', 1))
            customer_id = self.parse_arg(formdata, 'customer_id', defval=utils.get_uuid())
            order_id = self.parse_arg(formdata, 'order_id', defval=utils.get_uuid(), rule=rules.not_null)
            product_id = self.parse_arg(formdata, 'product_id', rule=rules.not_null)
            node_id = self.parse_arg(formdata, 'node_id', rule=rules.not_null)
            area_id = self.parse_arg(formdata, 'area_id', defval='')
            agency_id = self.parse_arg(formdata, 'agency_id', defval='')
            realname = self.parse_arg(formdata, 'realname', defval=account_number)
            realname = realname or account_number
            password = self.parse_arg(formdata, 'password', rule=rules.not_null)
            ip_address = self.parse_arg(formdata, 'ip_address', defval='')
            idcard = self.parse_arg(formdata, 'idcard', defval='')
            sex = self.parse_arg(formdata, 'sex', defval='1')
            age = self.parse_arg(formdata, 'age', defval='0')
            email = self.parse_arg(formdata, 'email', defval='')
            mobile = self.parse_arg(formdata, 'mobile', defval='')
            address = self.parse_arg(formdata, 'address', defval='')
            customer_desc = self.parse_arg(formdata, 'customer_desc', defval='')
            accept_source = self.parse_arg(formdata, 'accept_source', defval='console')
            expire_date = self.parse_arg(formdata, 'expire_date', rule=rules.is_date)
            months = self.parse_arg(formdata, 'months', defval='0', rule=rules.is_number)
            days = self.parse_arg(formdata, 'days', defval='0', rule=rules.is_number)
            fee_value = self.parse_arg(formdata, 'fee_value', rule=rules.is_rmb)
            giftflows = self.parse_arg(formdata, 'giftflows', defval='0', rule=rules.is_number3)
            giftdays = self.parse_arg(formdata, 'giftdays', defval='0', rule=rules.is_number)
            charge_code = self.parse_arg(formdata, 'charge_code', defval='')
            builder_name = self.parse_arg(formdata, 'builder_name', defval='')
            status = self.parse_arg(formdata, 'status', defval='1', rule=rules.is_number)
            wechat_oid = self.parse_arg(formdata, 'wechat_oid', defval='')
            vcard_code = self.parse_arg(formdata, 'vcard_code', defval='')
            vcard_pwd = self.parse_arg(formdata, 'vcard_pwd', defval='')
            if not self.check_data(formdata):
                return False
            product = self.db.query(models.TrProduct).get(product_id)
            vcard = None
            if vcard_code and vcard_pwd:
                vcard = self.db.query(models.TrValCard).get(vcard_code)
                if not self.check_vcard(vcard, vcard_pwd, product):
                    return False
            if hasattr(self.operator, 'agency_id') and self.operator.agency_id is not None:
                agency_id = self.operator.agency_id
            customer = models.TrCustomer()
            customer.customer_id = customer_id
            customer.node_id = node_id
            customer.area_id = area_id
            customer.agency_id = agency_id
            customer.realname = utils.safeunicode(realname)
            customer.customer_name = account_number
            customer.password = md5(password.encode()).hexdigest()
            customer.idcard = idcard
            customer.sex = sex
            customer.age = age
            customer.email = email
            customer.mobile = mobile
            customer.address = address
            customer.create_time = utils.get_currtime()
            customer.update_time = utils.get_currtime()
            customer.email_active = 0
            customer.mobile_active = 0
            customer.active_code = utils.get_uuid()
            customer.customer_desc = customer_desc
            customer.wechat_oid = wechat_oid
            customer.sync_ver = tools.gen_sync_ver()
            self.db.add(customer)
            accept_log = models.TrAcceptLog()
            accept_log.id = utils.get_uuid()
            accept_log.accept_type = 'open'
            accept_log.accept_source = accept_source
            accept_log.account_number = account_number
            accept_log.accept_time = customer.create_time
            accept_log.operator_name = self.operator.operator_name
            accept_log.accept_desc = u'用户新开户：(%s)%s' % (customer.customer_name, customer.realname)
            accept_log.stat_year = accept_log.accept_time[0:4]
            accept_log.stat_month = accept_log.accept_time[0:7]
            accept_log.stat_day = accept_log.accept_time[0:10]
            accept_log.sync_ver = tools.gen_sync_ver()
            self.db.add(accept_log)
            order_fee = 0
            balance = 0
            expire_date = expire_date
            flow_length = 0
            if product.product_policy == PPMonth:
                order_fee = decimal.Decimal(product.fee_price) * decimal.Decimal(months)
                order_fee = int(order_fee.to_integral_value())
            if product.product_policy == PPDay:
                order_fee = decimal.Decimal(product.fee_price) * decimal.Decimal(days)
                order_fee = int(order_fee.to_integral_value())
            elif product.product_policy == APMonth:
                order_fee = 0
            elif product.product_policy in (BOMonth, BODay):
                order_fee = int(product.fee_price)
            elif product.product_policy == BOFlows:
                order_fee = int(product.fee_price)
                flow_length = int(product.fee_flows)
            order = models.TrCustomerOrder()
            order.order_id = order_id
            order.customer_id = customer.customer_id
            order.product_id = product.id
            order.account_number = account_number
            order.order_fee = order_fee
            order.actual_fee = utils.yuan2fen(fee_value)
            order.pay_status = pay_status
            order.accept_id = accept_log.id
            order.order_source = accept_log.accept_source
            order.create_time = customer.create_time
            order.order_desc = u'用户新开账号'
            order.stat_year = order.create_time[0:4]
            order.stat_month = order.create_time[0:7]
            order.stat_day = order.create_time[0:10]
            order.sync_ver = tools.gen_sync_ver()
            self.db.add(order)
            if vcard:
                vcard.status = 2
                vcard.use_time = utils.get_currtime()
                vcard.customer_id = customer.customer_id
            if agency_id and pay_status == 1:
                agency = self.db.query(models.TrAgency).get(agency_id)
                if agency.amount < order.actual_fee:
                    self.last_error = u'代理商预存款余额不足'
                    return False
                agency_share = models.TrAgencyShare()
                agency_share.id = utils.get_uuid()
                agency_share.agency_id = agency_id
                agency_share.order_id = order.order_id
                agency_share.share_rate = agency.share_rate
                sfee = decimal.Decimal(order.actual_fee) * decimal.Decimal(agency.share_rate) / decimal.Decimal(100)
                sfee = int(sfee.to_integral_value())
                agency_share.share_fee = sfee
                agency_share.create_time = utils.get_currtime()
                agency_share.sync_ver = tools.gen_sync_ver()
                self.db.add(agency_share)
                agency.amount -= order.actual_fee
                aorder = models.TrAgencyOrder()
                aorder.id = utils.get_uuid()
                aorder.agency_id = agency.id
                aorder.fee_type = 'cost'
                aorder.fee_value = -order.actual_fee
                aorder.fee_total = agency.amount
                aorder.fee_desc = u'用户 %s 开通扣费' % account_number
                aorder.create_time = agency_share.create_time
                aorder.sync_ver = tools.gen_sync_ver()
                self.db.add(aorder)
                agency.amount += agency_share.share_fee
                aorder2 = models.TrAgencyOrder()
                aorder2.id = utils.get_uuid()
                aorder2.agency_id = agency.id
                aorder2.fee_type = 'share'
                aorder2.fee_value = agency_share.share_fee
                aorder2.fee_total = agency.amount
                aorder2.fee_desc = u'用户 %s 开通分成(%s%%)' % (account_number, agency.share_rate)
                aorder2.create_time = agency_share.create_time
                aorder2.sync_ver = tools.gen_sync_ver()
                self.db.add(aorder2)
            charge_value = 0
            if charge_code:
                charge_log = models.TrChargeLog()
                charge_log.id = utils.get_uuid()
                charge_log.order_id = order.order_id
                charge_log.charge_code = charge_code
                charge_log.operator_name = accept_log.operator_name
                charge_log.operate_time = order.create_time
                charge_log.sync_ver = tools.gen_sync_ver()
                self.db.add(charge_log)
                charge_value = int(self.db.query(models.TrCharges).get(charge_code).charge_value or 0)
            account = models.TrAccount()
            account.account_number = account_number
            account.ip_address = ip_address
            account.customer_id = customer.customer_id
            account.product_id = order.product_id
            account.install_address = customer.address
            account.mac_addr = ''
            account.password = self.aes.encrypt(password)
            account.status = status
            if billing_type == 0:
                account.status = UsrPreAuth
            if pay_status == 0:
                account.status = UsrPadding
            account.balance = balance - charge_value
            account.time_length = int(product.fee_times)
            account.flow_length = flow_length
            account.expire_date = expire_date
            account.user_concur_number = product.concur_number
            account.bind_mac = product.bind_mac
            account.bind_vlan = product.bind_vlan
            account.vlan_id1 = 0
            account.vlan_id2 = 0
            account.create_time = customer.create_time
            account.update_time = customer.create_time
            account.account_desc = customer.customer_desc
            account.sync_ver = tools.gen_sync_ver()
            self.db.add(account)
            if pay_status == 0:
                order.before_account_data = self.warp_account_data(account, status=UsrPadding)
            order.after_account_data = self.warp_account_data(account, status=1)
            order.order_desc = u'用户新开账号,赠送天数：%s, 收费项金额：%s' % (giftdays, utils.fen2yuan(charge_value))
            issues = None
            builder_phone = None
            if builder_name and pay_status == 1:
                builder_phone = self.db.query(models.TrBuilder.builder_phone).filter_by(builder_name=builder_name).scalar()
                issues = models.TrIssues()
                issues.id = utils.get_uuid()
                issues.account_number = account.account_number
                issues.issues_type = '0'
                issues.content = u'用户新开账号, 请前往安装'
                issues.builder_name = builder_name
                issues.status = 0
                issues.operator_name = self.operator.operator_name
                issues.date_time = utils.get_currtime()
                issues.sync_ver = tools.gen_sync_ver()
                self.db.add(issues)
            opsdesc = u'用户新开账号 %s, 赠送天数：%s, 收费项金额：%s' % (account.account_number, giftdays, utils.fen2yuan(charge_value))
            self.add_oplog(opsdesc)
            self.db.commit()
            dispatch.pub(ACCOUNT_OPEN_EVENT, account.account_number, async=True)
            if issues and builder_phone:
                dispatch.pub(ISSUES_ASSIGN_EVENT, issues.account_number, builder_phone, async=True)
            self.update_routeros_sync_event(account_number, password, product_id, node_id)
            return True
        except Exception as err:
            self.db.rollback()
            traceback.print_exc()
            self.last_error = u'客户开户操作失败:%s' % utils.safeunicode(err)
            logger.error(self.last_error, tag='customer_add_error', username=formdata.get('account_number'))
            return False

        return

    @logparams
    def batch_add(self, formdata, **kwargs):
        try:
            opennum = int(formdata.get('opennum', 100))
            if opennum > 1000:
                opennum = 1000
            user_prefix = formdata.get('user_prefix', datetime.datetime.now().strftime('%Y%m%d'))
            suffix_len = int(formdata.get('suffix_len', 4))
            start_num = int(formdata.get('start_num', 1))
            pwd_type = int(formdata.get('pwd_type', 0))
            product_id = self.parse_arg(formdata, 'product_id', rule=rules.not_null)
            expire_date = self.parse_arg(formdata, 'expire_date', rule=rules.is_date)
            node_id = self.parse_arg(formdata, 'node_id', rule=rules.not_null)
            area_id = self.parse_arg(formdata, 'area_id', defval='')
            for num in xrange(start_num, opennum + start_num):
                account_number = '%s%s' % (user_prefix, string.rjust(str(num), suffix_len, '0'))
                customer = models.TrCustomer()
                customer.customer_id = utils.get_uuid()
                customer.node_id = node_id
                customer.area_id = area_id
                customer.agency_id = None
                customer.realname = account_number
                customer.customer_name = account_number
                customer.password = md5(str(random.randint(999999, 99999999))).hexdigest()
                customer.idcard = ''
                customer.sex = '1'
                customer.age = '0'
                customer.email = ''
                customer.mobile = '000000'
                customer.address = ''
                customer.create_time = utils.get_currtime()
                customer.update_time = utils.get_currtime()
                customer.email_active = 0
                customer.mobile_active = 0
                customer.active_code = utils.get_uuid()
                customer.customer_desc = u'批量生成客户'
                customer.sync_ver = tools.gen_sync_ver()
                self.db.add(customer)
                accept_log = models.TrAcceptLog()
                accept_log.id = utils.get_uuid()
                accept_log.accept_type = 'open'
                accept_log.accept_source = 'console'
                accept_log.account_number = account_number
                accept_log.accept_time = customer.create_time
                accept_log.operator_name = self.operator.operator_name
                accept_log.accept_desc = u'用户新开户：%s' % customer.customer_name
                accept_log.stat_year = accept_log.accept_time[0:4]
                accept_log.stat_month = accept_log.accept_time[0:7]
                accept_log.stat_day = accept_log.accept_time[0:10]
                accept_log.sync_ver = tools.gen_sync_ver()
                self.db.add(accept_log)
                product = self.db.query(models.TrProduct).get(product_id)
                order = models.TrCustomerOrder()
                order.order_id = utils.get_uuid()
                order.customer_id = customer.customer_id
                order.product_id = product.id
                order.account_number = account_number
                if product.product_policy in (PPTimes,
                 PPFlow,
                 PPMonth,
                 PPDay):
                    order.order_fee = 0
                else:
                    order.order_fee = product.fee_price
                order.actual_fee = 0
                order.pay_status = 1
                order.accept_id = accept_log.id
                order.order_source = accept_log.accept_source
                order.create_time = customer.create_time
                order.order_desc = u'用户批量开通账号'
                order.stat_year = order.create_time[0:4]
                order.stat_month = order.create_time[0:7]
                order.stat_day = order.create_time[0:10]
                order.sync_ver = tools.gen_sync_ver()
                self.db.add(order)
                account = models.TrAccount()
                account.account_number = account_number
                account.ip_address = ''
                account.customer_id = customer.customer_id
                account.product_id = order.product_id
                account.install_address = ''
                account.mac_addr = ''
                if pwd_type == 1 and password not in (None, ''):
                    account.password = self.aes.encrypt(password)
                else:
                    account.password = self.aes.encrypt(str(random.randint(999999, 9999999)))
                account.status = 0
                account.balance = 0
                account.time_length = int(product.fee_times)
                account.flow_length = int(product.fee_flows)
                account.expire_date = expire_date
                account.user_concur_number = product.concur_number
                account.bind_mac = product.bind_mac
                account.bind_vlan = product.bind_vlan
                account.vlan_id1 = 0
                account.vlan_id2 = 0
                account.create_time = customer.create_time
                account.update_time = customer.create_time
                account.account_desc = customer.customer_desc
                account.sync_ver = tools.gen_sync_ver()
                self.db.add(account)

            self.add_oplog(u'批量开户总数 %s' % opennum)
            self.db.commit()
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='customer_batch_add_error')
            traceback.print_exc()
            self.last_error = u'批量开户操作失败:%s' % utils.safeunicode(err.message)
            return False

        return

    @logparams
    def add_wlan_user(self, domain, phone, vcode, user_desc):
        try:
            if not domain:
                raise ValueError(u'认证域不能为空')
            domain_ins = self.db.query(models.TrDomain).filter_by(domain_code=domain).first()
            if not domain_ins:
                raise ValueError(u'认证域 %s 不存在' % domain)
            _now = datetime.datetime.now()
            node_id = self.db.query(models.TrNode.id).limit(1).scalar()
            if not node_id:
                raise ValueError(u'必须创建运营区域')
            product_id = self.db.query(models.TrDomainAttr.attr_value).filter_by(domain_code=domain, attr_name='wlan_product_id').scalar()
            if not product_id:
                raise ValueError(u'认证域 [%s] 未提供自助热点资费套餐' % domain)
            if not self.db.query(models.TrProduct).get(product_id):
                raise ValueError(u'资费不存在')
            account = self.db.query(models.TrAccount).get(phone)
            if account:
                account.password = self.aes.encrypt(vcode)
                self.db.commit()
            else:
                formdata = Storage({'account_number': phone,
                 'password': vcode,
                 'node_id': node_id,
                 'area_id': '',
                 'idcard': phone,
                 'agency_id': None,
                 'builder_name': None,
                 'giftflows': '0',
                 'giftdays': '0',
                 'time_length': '1',
                 'flow_length': '0.5',
                 'expire_date': (_now + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                 'fee_value': '0.00',
                 'status': '1',
                 'realname': phone,
                 'address': u'wlan portal',
                 'ip_address': None,
                 'product_id': product_id,
                 'mobile': phone,
                 'months': '1',
                 'customer_desc': user_desc})
                self.add(formdata)
            return True
        except Exception as err:
            import traceback
            traceback.print_exc()
            self.last_error = u'热点用户注册失败:%s' % utils.safeunicode(err)
            logger.error(self.last_error, tag='wlan_customer_add_error', trace='wlan', username=phone)
            return False

        return
