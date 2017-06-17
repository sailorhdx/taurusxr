#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
from tablib import Dataset
from toughradius.modules import models
from toughradius.modules.base import authenticated
from toughradius.modules.customer import customer_forms
from toughradius.modules.customer.customer import CustomerHandler
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules.settings import *

@permit.route('/admin/customer/attrfile/(\\w+)/(\\w+)')

class AttrfileGetHandler(CustomerHandler):

    def get(self, username, attrname):
        if not self.current_user:
            return self.render_error(msg=u'未授权的访问')
        attrfile = self.db.query(models.TrAccountAttr.attr_value).filter_by(account_number=username, attr_name=attrname).limit(1).scalar()
        if os.path.exists(attrfile):
            if attrname in ('IDCARD1', 'IDCARD2'):
                self.set_header('Content-Type', 'image/jpeg')
            with open(attrfile, 'rb') as df:
                for line in df:
                    self.write(line)

        else:
            self.write('file %s not exists' % attrfile)


@permit.route('/admin/customer/detail', u'用户详情', MenuUser, order=1.2)

class CustomerDetailHandler(CustomerHandler):

    def showpwd(self, password):
        try:
            return self.aes.decrypt(password)
        except:
            return ''

    @authenticated
    def get(self):
        account_number = self.get_argument('account_number')
        user = self.db.query(models.TrCustomer.realname, models.TrNode.node_name, models.TrArea.area_name, models.TrAgency.agency_name, models.TrAccount.customer_id, models.TrAccount.account_number, models.TrAccount.password, models.TrAccount.expire_date, models.TrAccount.balance, models.TrAccount.time_length, models.TrAccount.flow_length, models.TrAccount.user_concur_number, models.TrAccount.status, models.TrAccount.mac_addr, models.TrAccount.vlan_id1, models.TrAccount.vlan_id2, models.TrAccount.ip_address, models.TrAccount.bind_mac, models.TrAccount.bind_vlan, models.TrAccount.ip_address, models.TrAccount.install_address, models.TrAccount.last_pause, models.TrAccount.create_time, models.TrAccount.update_time, models.TrProduct.product_name, models.TrProduct.product_policy).outerjoin(models.TrArea, models.TrCustomer.area_id == models.TrArea.id).outerjoin(models.TrAgency, models.TrCustomer.agency_id == models.TrAgency.id).filter(models.TrProduct.id == models.TrAccount.product_id, models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrCustomer.node_id == models.TrNode.id, models.TrAccount.account_number == account_number).first()
        attrs = self.db.query(models.TrAccountAttr).filter_by(account_number=account_number)
        customer = self.db.query(models.TrCustomer).get(user.customer_id)
        orders = self.db.query(models.TrCustomerOrder.order_id, models.TrCustomerOrder.order_id, models.TrCustomerOrder.product_id, models.TrCustomerOrder.account_number, models.TrCustomerOrder.order_fee, models.TrCustomerOrder.actual_fee, models.TrCustomerOrder.pay_status, models.TrCustomerOrder.create_time, models.TrCustomerOrder.order_desc, models.TrProduct.product_name, models.TrCharges.charge_name, models.TrCharges.charge_value, models.TrAgencyShare.share_rate, models.TrAgencyShare.share_fee).outerjoin(models.TrChargeLog, models.TrCustomerOrder.order_id == models.TrChargeLog.order_id).outerjoin(models.TrCharges, models.TrChargeLog.charge_code == models.TrCharges.charge_code).outerjoin(models.TrAgencyShare, models.TrCustomerOrder.order_id == models.TrAgencyShare.order_id).filter(models.TrProduct.id == models.TrCustomerOrder.product_id, models.TrCustomerOrder.account_number == account_number).order_by(models.TrCustomerOrder.create_time.desc())
        accepts = self.db.query(models.TrAcceptLog.id, models.TrAcceptLog.accept_type, models.TrAcceptLog.accept_time, models.TrAcceptLog.accept_desc, models.TrAcceptLog.operator_name, models.TrAcceptLog.accept_source, models.TrAcceptLog.account_number, models.TrCustomer.node_id, models.TrNode.node_name).filter(models.TrAcceptLog.account_number == models.TrAccount.account_number, models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrNode.id == models.TrCustomer.node_id, models.TrAcceptLog.account_number == account_number).order_by(models.TrAcceptLog.accept_time.desc())
        issues_list = self.db.query(models.TrIssues).filter(models.TrIssues.account_number == account_number).order_by(models.TrIssues.date_time.desc())
        userlogs = self.logtrace.list_userlog(user.account_number) or []
        vcards = self.db.query(models.TrValCard).filter_by(customer_id=customer.customer_id)
        get_orderid = lambda aid: self.db.query(models.TrCustomerOrder.order_id).filter_by(accept_id=aid).scalar()
        get_note_id = lambda oid: self.db.query(models.TrCustomerNote.note_id).filter_by(order_id=oid).scalar()
        get_attr_val = lambda an: self.db.query(models.TrAccountAttr.attr_value).filter_by(account_number=account_number, attr_name=an).scalar()
        get_basename = lambda fname: os.path.basename(fname)
        type_map = ACCEPT_TYPES
        return self.render('customer_detail.html', customer=customer, attrs=attrs, user=user, orders=orders, accepts=accepts, issues_list=issues_list, userlogs=userlogs, vcards=vcards, type_map=type_map, get_note_id=get_note_id, get_orderid=get_orderid, get_attr_val=get_attr_val, get_basename=get_basename, showpwd=self.showpwd)