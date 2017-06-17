#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import decimal
import datetime
from toughradius.modules import models
from toughradius.modules.base import authenticated
from toughradius.modules.customer import customer_forms
from toughradius.modules.customer.customer import CustomerHandler
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, logger, dispatch
from toughradius.modules.settings import *
from toughradius.modules.events import settings as evset

@permit.suproute('/admin/customer/delete', u'用户资料删除', MenuUser, order=1.5)

class CustomerDeleteHandler(CustomerHandler):

    @authenticated
    def get(self):
        customer_id = self.get_argument('customer_id')
        if not customer_id:
            return self.render_error(msg=u'无效的客户ID')
        account = self.db.query(models.TrAccount).filter_by(customer_id=customer_id).first()
        account_number = account.account_number
        self.db.query(models.TrAcceptLog).filter_by(account_number=account_number).delete()
        self.db.query(models.TrAccountAttr).filter_by(account_number=account_number).delete()
        self.db.query(models.TrBilling).filter_by(account_number=account_number).delete()
        self.db.query(models.TrTicket).filter_by(account_number=account_number).delete()
        self.db.query(models.TrOnline).filter_by(account_number=account_number).delete()
        self.db.query(models.TrAccount).filter_by(account_number=account_number).delete()
        self.db.query(models.TrCustomerOrder).filter_by(account_number=account_number).delete()
        self.add_oplog(u'删除用户账号%s' % account_number)
        self.db.query(models.TrCustomer).filter_by(customer_id=customer_id).delete()
        self.add_oplog(u'删除用户资料 %s' % customer_id)
        self.db.commit()
        dispatch.pub(evset.ACCOUNT_DELETE_EVENT, account_number, async=True)
        dispatch.pub(evset.CACHE_DELETE_EVENT, account_cache_key(account_number), async=True)
        dispatch.pub(evset.DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAcceptLog.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(evset.DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAccountAttr.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(evset.DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrBilling.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(evset.DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOnline.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(evset.DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAccount.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(evset.DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrCustomerOrder.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(evset.DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrCustomer.__tablename__, dict(customer_id=customer_id)), async=True)
        return self.redirect('/admin/customer')
