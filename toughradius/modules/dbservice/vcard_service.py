#!/usr/bin/env python
# coding=utf-8
import json
import datetime
from toughradius.modules.settings import *
from hashlib import md5
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.common import tools
from toughradius.toughlib import utils, dispatch, logger
from toughradius.toughlib.storage import Storage
from toughradius.modules.dbservice import BaseService
from toughradius.modules.dbservice import logparams

class VcardService(BaseService):

    def get_next_bn(self):
        next_card_bn = tools.gen_random_num(9)
        if self.db.query(models.TrValCard.card_bn).filter_by(card_bn=next_card_bn).count() > 0:
            return self.get_next_bn()
        else:
            return next_card_bn

    def batchadd(self, formdata, **kwargs):
        try:
            batch_bn = self.get_next_bn()
            batch_num = int(formdata.num)
            if batch_num > 100:
                raise ValueError(u'最大只能发行300个充值卡')
            if formdata.card_type not in ('product', 'balance', 'timelen', 'flowlen'):
                raise ValueError(u'无效的充值卡类型')
            for sn in range(1001, batch_num + 1001):
                vcard = models.TrValCard()
                vcard.card_code = '{0}{1}'.format(batch_bn, sn)
                vcard.card_type = formdata.card_type
                vcard.card_bn = batch_num
                vcard.card_pwd = self.aes.encrypt(tools.gen_random_num(7))
                vcard.product_tag = ''
                vcard.credit = 0
                vcard.flowlen = 0
                vcard.timelen = 0
                vcard.status = 0
                vcard.expire_date = formdata.expire_date
                vcard.create_time = utils.get_currtime()
                if formdata.card_type == 'product':
                    vcard.product_tag = formdata.product_tag
                if formdata.card_type == 'balance':
                    vcard.credit = formdata.credit
                if formdata.card_type == 'flowlen':
                    vcard.flowlen = formdata.flowlen
                if formdata.card_type == 'timelen':
                    vcard.timelen = formdata.timelen
                vcard.fee_price = utils.fen2yuan(int(formdata.fee_price) * 100)
                self.db.add(vcard)

            self.add_oplog(u'批量发行充值卡：数量=%s' % batch_num)
            self.db.commit()
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err)
            self.last_error = u'充值卡发行失败:%s' % utils.safeunicode(err)
            return False

    def batch_deactive(self, vcardcodes, **kwargs):
        try:
            vcardcodes = [ vc for vc in vcardcodes if vc ]
            if not vcardcodes:
                raise ValueError(u'没有需要处理的卡')
            for vc in vcardcodes:
                up_params = {'status': 0,
                 'active_time': ''}
                self.db.query(models.TrValCard).filter_by(card_code=vc, status=1).update(up_params)

            self.add_oplog(u'批量取消激活充值卡：数量=%s' % len(vcardcodes))
            self.db.commit()
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err)
            self.last_error = u'充值卡取消激活失败:%s' % utils.safeunicode(err)
            return False

    def batch_active(self, vcardcodes, **kwargs):
        try:
            vcardcodes = [ vc for vc in vcardcodes if vc ]
            if not vcardcodes:
                raise ValueError(u'没有需要处理的卡')
            for vc in vcardcodes:
                up_params = {'status': 1,
                 'active_time': utils.get_currtime()}
                self.db.query(models.TrValCard).filter_by(card_code=vc, status=0).update(up_params)

            self.add_oplog(u'批量激活充值卡：数量=%s' % len(vcardcodes))
            self.db.commit()
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err)
            self.last_error = u'充值卡激活失败:%s' % utils.safeunicode(err)
            return False

    def batch_delete(self, vcardcodes, **kwargs):
        try:
            vcardcodes = [ vc for vc in vcardcodes if vc ]
            if not vcardcodes:
                raise ValueError(u'没有需要处理的卡')
            for vc in vcardcodes:
                self.db.query(models.TrValCard).filter_by(card_code=vc, status=0).delete()

            self.add_oplog(u'批量删除充值卡：数量=%s' % len(vcardcodes))
            self.db.commit()
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err)
            self.last_error = u'充值卡删除失败:%s' % utils.safeunicode(err)
            return False