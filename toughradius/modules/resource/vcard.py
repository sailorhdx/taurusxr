#!/usr/bin/env python
# coding=utf-8
import os
import time
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules.resource import vcard_forms
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, dispatch
from toughradius.toughlib import redis_cache
from toughradius.common import tools
from toughradius.modules import events
from tablib import Dataset
from toughradius.modules.settings import *
from toughradius.modules.dbservice.vcard_service import VcardService
if os.environ.get('LICENSE_TYPE') != 'community':

    @permit.suproute('/admin/vcard', u'充值卡管理', MenuRes, order=4.0, is_menu=True)

    class VcardListHandler(BaseHandler):

        def showpwd(self, password):
            try:
                return self.aes.decrypt(password)
            except:
                return ''

        @authenticated
        def get(self):
            self.post()

        @authenticated
        def post(self):
            card_code = self.get_argument('card_code', None)
            card_type = self.get_argument('card_type', None)
            product_tag = self.get_argument('product_tag', None)
            status = self.get_argument('status', None)
            query_begin_time = self.get_argument('query_begin_time', None)
            query_end_time = self.get_argument('query_end_time', None)
            _query = self.db.query(models.TrValCard)
            if card_code:
                _query = _query.filter(models.TrValCard.card_code == card_code)
            if card_type:
                _query = _query.filter(models.TrValCard.card_type == card_type)
            if product_tag:
                _query = _query.filter(models.TrValCard.product_tag == product_tag)
            if status:
                if status == 'expire':
                    _query = _query.filter(models.TrValCard.expire_date < utils.get_currdate())
                else:
                    _query = _query.filter(models.TrValCard.status == int(status))
            if query_begin_time:
                _query = _query.filter(models.TrValCard.active_time >= '{} 00:00:00'.format(query_begin_time))
            if query_end_time:
                _query = _query.filter(models.TrValCard.active_time <= '{} 23:59:59'.format(query_end_time))
            page_data = self.get_page_data(_query)
            if self.request.path == '/admin/vcard':
                self.render('vcard_list.html', page_data=page_data)
            elif self.request.path == '/admin/vcard/export':
                data = Dataset()
                data.append((u'卡号', u'密码', u'卡类型', u'卡状态', u'资费标签', u'储值余额', u'储值流量', u'储值时长', u'零售价格', u'过期时间', u'激活时间'))
                for i in _query:
                    data.append((i.card_code,
                     self.aes.decrypt(i.card_pwd),
                     i.card_type,
                     vcard_forms.cardstatus.get(i.status),
                     i.product_tag,
                     i.credit,
                     i.flowlen,
                     i.timelen,
                     i.fee_price,
                     i.expire_date,
                     i.active_time))

                name = u'VCARD-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.xls'
                self.export_file(name, data)
            return


    @permit.suproute('/admin/vcard/export', u'充值卡导出', MenuRes, order=4.0001)

    class VcardExportHandler(VcardListHandler):
        pass


    @permit.suproute('/admin/vcard/batchadd', u'发行充值卡', MenuRes, order=4.0001)

    class VcardBatchAddHandler(BaseHandler):

        @authenticated
        def get(self):
            form = vcard_forms.vcard_batch_form()
            form.credit.set_value(0)
            form.flowlen.set_value(0)
            form.timelen.set_value(0)
            form.fee_price.set_value(0)
            self.render('vcard_form.html', form=form)

        @authenticated
        def post(self):
            form = vcard_forms.vcard_batch_form()
            if not form.validates(source=self.get_params()):
                return self.render('vcard_form.html', form=form)
            manager = VcardService(self.db, aes=self.aes, operator=self.current_user, config=self.settings.config)
            ret = manager.batchadd(form.d)
            if not ret:
                return self.render('vcard_form.html', form=form, msg=manager.last_error)
            self.redirect('/admin/vcard', permanent=False)


    @permit.suproute('/admin/vcard/active', u'批量激活充值卡', MenuRes, order=4.0002)

    class VcardActiveHandler(BaseHandler):

        @authenticated
        def post(self):
            vcardcodes = self.get_argument('vcardcodes', '')
            manager = VcardService(self.db, aes=self.aes, operator=self.current_user, config=self.settings.config)
            ret = manager.batch_active(vcardcodes.split(','))
            if not ret:
                return self.render_json(code=1, msg=manager.last_error)
            self.render_json(code=0, msg=u'批量卡激活完成 (只有初始化状态的卡才会被激活)')


    @permit.suproute('/admin/vcard/deactive', u'批量取消激活充值卡', MenuRes, order=4.0002)

    class VcardDeActiveHandler(BaseHandler):

        @authenticated
        def post(self):
            vcardcodes = self.get_argument('vcardcodes', '')
            manager = VcardService(self.db, aes=self.aes, operator=self.current_user, config=self.settings.config)
            ret = manager.batch_deactive(vcardcodes.split(','))
            if not ret:
                return self.render_json(code=1, msg=manager.last_error)
            self.render_json(code=0, msg=u'批量卡取消激活完成 (只有激活的卡才会被操作)')


    @permit.suproute('/admin/vcard/delete', u'批量删除充值卡', MenuRes, order=4.0003)

    class VcardDeleteHandler(BaseHandler):

        @authenticated
        def post(self):
            vcardcodes = self.get_argument('vcardcodes', '')
            manager = VcardService(self.db, aes=self.aes, operator=self.current_user, config=self.settings.config)
            ret = manager.batch_delete(vcardcodes.split(','))
            if not ret:
                return self.render_json(code=1, msg=manager.last_error)
            self.render_json(code=0, msg=u'批量删除卡完成 (只有初始化状态的才会被删除)')