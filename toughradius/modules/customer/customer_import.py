#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
from tablib import Dataset
from hashlib import md5
from toughradius.modules import models
from toughradius.modules.customer import customer_forms
from toughradius.modules.base import authenticated
from toughradius.modules.customer.customer import CustomerHandler
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, logger
from toughradius.modules.settings import *
from toughradius.common import tools

@permit.suproute('/admin/customer/import', u'用户资料导入', MenuUser, order=1.3, is_menu=True)

class CustomerImportHandler(CustomerHandler):

    @authenticated
    def get(self):
        form = customer_forms.customer_import_form()
        return self.render('customer_import_form.html', form=form)

    def get_node_id(self, node_name, ncache = {}):
        if node_name in ncache:
            return ncache[node_name]
        return self.db.query(models.TrNode.id).filter_by(node_name=node_name).limit(1).scalar()

    def get_area_id(self, area_name, acache = {}):
        if area_name in acache:
            return acache[area_name]
        return self.db.query(models.TrArea.id).filter_by(area_name=area_name).limit(1).scalar()

    def get_product_id(self, product_name, pcache = {}):
        if product_name in pcache:
            return pcache[product_name]
        return self.db.query(models.TrProduct.id).filter_by(product_name=product_name).limit(1).scalar()

    @authenticated
    def post(self):
        node_cache = {}
        area_cache = {}
        product_cache = {}
        accounts = [ a.account_number for a in self.db.query(models.TrAccount.account_number) ]
        iform = customer_forms.customer_import_form()
        f = self.request.files['import_file'][0]
        try:
            impctx = utils.safeunicode(f['body'])
        except Exception as err:
            logger.exception(err)
            self.render_error(msg=u'文件格式错误： %s' % utils.safeunicode(err))
            return

        lines = impctx.split('\n')
        _num = 0
        impusers = []
        for line in lines:
            _num += 1
            line = line.strip()
            if not line or u'用户姓名' in line:
                continue
            attr_array = line.split(',')
            if len(attr_array) < 13:
                return self.render('customer_import_form.html', form=iform, msg=u'第 %s  行错误: 用户字段必须是14个 ' % _num)
            if attr_array[7] in accounts:
                continue
            vform = customer_forms.customer_import_vform()
            vform.fill(**dict(realname=utils.safeunicode(attr_array[0]), node=utils.safeunicode(attr_array[1]), area=utils.safeunicode(attr_array[2]), product=utils.safeunicode(attr_array[3]), idcard=attr_array[4], mobile=attr_array[5], address=utils.safeunicode(attr_array[6]), account_number=attr_array[7], password=attr_array[8], begin_date=attr_array[9], expire_date=attr_array[10], time_length=utils.hour2sec(attr_array[11]), flow_length=utils.mb2kb(attr_array[12])))
            impusers.append(vform)

        _unums = 0
        for form in impusers:
            try:
                node_id = self.get_node_id(form.d.node, node_cache)
                if not node_id:
                    raise ValueError(u'区域:%s不存在' % utils.safeunicode(form.d.node))
                area_id = self.get_area_id(form.d.area, area_cache)
                if not area_id:
                    raise ValueError(u'社区:%s不存在' % utils.safeunicode(form.d.area))
                product_id = self.get_product_id(form.d.product, product_cache)
                if not product_id:
                    raise ValueError(u'资费:%s不存在' % utils.safeunicode(form.d.product))
                customer = models.TrCustomer()
                customer.customer_id = utils.get_uuid()
                customer.node_id = node_id
                customer.area_id = area_id
                customer.realname = form.d.realname
                customer.idcard = form.d.idcard
                customer.customer_name = form.d.account_number
                customer.password = md5(form.d.password.encode()).hexdigest()
                customer.sex = '1'
                customer.age = '0'
                customer.email = ''
                customer.mobile = form.d.mobile
                customer.address = form.d.address
                customer.create_time = form.d.begin_date + ' 00:00:00'
                customer.update_time = utils.get_currtime()
                customer.email_active = 0
                customer.mobile_active = 0
                customer.active_code = utils.get_uuid()
                customer.sync_ver = tools.gen_sync_ver()
                self.db.add(customer)
                accept_log = models.TrAcceptLog()
                accept_log.id = utils.get_uuid()
                accept_log.accept_type = 'open'
                accept_log.accept_source = 'console'
                _desc = u'用户导入账号：%s' % form.d.account_number
                accept_log.accept_desc = _desc
                accept_log.account_number = form.d.account_number
                accept_log.accept_time = customer.update_time
                accept_log.operator_name = self.current_user.username
                accept_log.stat_year = accept_log.accept_time[0:4]
                accept_log.stat_month = accept_log.accept_time[0:7]
                accept_log.stat_day = accept_log.accept_time[0:10]
                accept_log.sync_ver = tools.gen_sync_ver()
                self.db.add(accept_log)
                self.db.flush()
                self.db.refresh(accept_log)
                order_fee = 0
                actual_fee = 0
                balance = 0
                time_length = 0
                flow_length = 0
                expire_date = form.d.expire_date
                product = self.db.query(models.TrProduct).get(product_id)
                if product.product_policy == BOTimes:
                    time_length = utils.hour2sec(form.d.time_length)
                elif product.product_policy == BOFlows:
                    flow_length = utils.gb2kb(form.d.flow_length)
                elif product.product_policy in (PPTimes, PPFlow):
                    balance = utils.yuan2fen(form.d.balance)
                    expire_date = MAX_EXPIRE_DATE
                order = models.TrCustomerOrder()
                order.id = utils.get_uuid()
                order.order_id = utils.gen_order_id()
                order.customer_id = customer.customer_id
                order.product_id = product.id
                order.account_number = form.d.account_number
                order.order_fee = order_fee
                order.actual_fee = actual_fee
                order.pay_status = 1
                order.accept_id = accept_log.id
                order.order_source = 'console'
                order.create_time = customer.update_time
                order.order_desc = u'用户导入开户'
                order.stat_year = order.create_time[0:4]
                order.stat_month = order.create_time[0:7]
                order.stat_day = order.create_time[0:10]
                order.sync_ver = tools.gen_sync_ver()
                self.db.add(order)
                account = models.TrAccount()
                account.id = utils.get_uuid()
                account.account_number = form.d.account_number
                account.customer_id = customer.customer_id
                account.product_id = order.product_id
                account.install_address = customer.address
                account.ip_address = ''
                account.mac_addr = ''
                account.password = self.aes.encrypt(form.d.password)
                account.status = 1
                account.balance = 0
                account.time_length = time_length
                account.flow_length = flow_length
                account.expire_date = expire_date
                account.user_concur_number = product.concur_number
                account.bind_mac = product.bind_mac
                account.bind_vlan = product.bind_vlan
                account.vlan_id1 = 0
                account.vlan_id2 = 0
                account.create_time = customer.create_time
                account.update_time = customer.update_time
                account.sync_ver = tools.gen_sync_ver()
                self.db.add(account)
                _unums += 1
            except Exception as e:
                self.db.rollback()
                logger.exception(e)
                return self.render('customer_import_form.html', form=iform, msg=u'导入数据错误 : %s' % utils.safeunicode(e))

        self.add_oplog(u'导入开户，用户数：%s' % _unums)
        self.db.commit()
        self.redirect('/admin/customer')