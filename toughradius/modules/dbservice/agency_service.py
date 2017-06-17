#!/usr/bin/env python
# coding=utf-8
import datetime
from toughradius.modules.settings import *
from hashlib import md5
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.toughlib import utils, dispatch, logger
from toughradius.modules.dbservice import BaseService
from toughradius.modules.dbservice import logparams
from toughradius.common import tools
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD

class AgencyService(BaseService):

    def add(self, formdata, **kwargs):
        try:
            if int(formdata.share_rate) > 100 or int(formdata.share_rate) < 0:
                raise ValueError(u'分成比例必须在0-100')
            if self.db.query(models.TrOperator.id).filter_by(operator_name=formdata.operator_name).count() > 0:
                raise ValueError(u'操作员已经存在')
            agency = models.TrAgency()
            agency.id = utils.get_uuid()
            agency.agency_name = formdata.agency_name
            agency.operator_name = formdata.operator_name
            agency.contact = formdata.contact
            agency.mobile = formdata.mobile
            agency.amount = utils.yuan2fen(formdata.amount)
            agency.share_rate = formdata.share_rate
            agency.create_time = utils.get_currtime()
            agency.update_time = agency.create_time
            agency.agency_desc = formdata.agency_desc
            agency.sync_ver = tools.gen_sync_ver()
            self.db.add(agency)
            self.db.flush()
            self.db.refresh(agency)
            aorder = models.TrAgencyOrder()
            aorder.id = utils.get_uuid()
            aorder.agency_id = agency.id
            aorder.fee_type = 'recharge'
            aorder.fee_value = agency.amount
            aorder.fee_total = agency.amount
            aorder.fee_desc = u'代理商 (%s) 开通预存余额' % utils.safeunicode(formdata.agency_name)
            aorder.create_time = utils.get_currtime()
            aorder.sync_ver = tools.gen_sync_ver()
            self.db.add(aorder)
            operator = models.TrOperator()
            operator.id = utils.get_uuid()
            operator.operator_name = formdata.operator_name
            operator.operator_pass = md5(formdata.operator_pass.encode()).hexdigest()
            operator.operator_type = 1
            operator.operator_desc = formdata.agency_name
            operator.operator_status = 0
            operator.sync_ver = tools.gen_sync_ver()
            self.db.add(operator)
            for node_id in kwargs.get('operator_nodes') or []:
                onode = models.TrOperatorNodes()
                onode.operator_name = formdata.operator_name
                onode.node_id = node_id
                onode.sync_ver = tools.gen_sync_ver()
                self.db.add(onode)

            for product_id in kwargs.get('operator_products') or []:
                oproduct = models.TrOperatorProducts()
                oproduct.operator_name = formdata.operator_name
                oproduct.product_id = product_id
                oproduct.sync_ver = tools.gen_sync_ver()
                self.db.add(oproduct)

            for path in kwargs.get('rule_item') or []:
                item = permit.get_route(path)
                if not item:
                    continue
                rule = models.TrOperatorRule()
                rule.id = utils.get_uuid()
                rule.operator_name = operator.operator_name
                rule.rule_name = item['name']
                rule.rule_path = item['path']
                rule.rule_category = item['category']
                rule.sync_ver = tools.gen_sync_ver()
                self.db.add(rule)

            self.add_oplog(u'创建代理商 %s' % utils.safeunicode(agency.agency_name))
            self.db.commit()
            for rule in self.db.query(models.TrOperatorRule).filter_by(operator_name=agency.operator_name):
                permit.bind_opr(rule.operator_name, rule.rule_path)

            return agency
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='agency_add_error')
            self.last_error = u'代理商创建失败:%s' % utils.safeunicode(err)
            return False

    @logparams
    def recharge(self, formdata, **kwargs):
        try:
            rfee = utils.yuan2fen(formdata.fee_value)
            if rfee <= 0:
                raise ValueError(u'充值金额必须大于0')
            agency = self.db.query(models.TrAgency).get(formdata.agency_id)
            agency.amount += rfee
            aorder = models.TrAgencyOrder()
            aorder.id = utils.get_uuid()
            aorder.agency_id = agency.id
            aorder.fee_type = 'recharge'
            aorder.fee_value = rfee
            aorder.fee_total = agency.amount
            aorder.fee_desc = u'代理商 (%s) 充值' % utils.safeunicode(agency.agency_name)
            aorder.create_time = utils.get_currtime()
            aorder.sync_ver = tools.gen_sync_ver()
            self.db.add(aorder)
            self.add_oplog(u'代理商(%s)充值' % utils.safeunicode(agency.agency_name))
            self.db.commit()
            return agency
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='agency_recharge_error')
            self.last_error = u'代理商充值失败:%s' % utils.safeunicode(err)
            return False

    def update(self, formdata, **kwargs):
        try:
            if int(formdata.share_rate) > 100 or int(formdata.share_rate) < 0:
                raise ValueError(u'分成比例必须在1-100')
            agency = self.db.query(models.TrAgency).get(formdata.agency_id)
            agency.agency_name = formdata.agency_name
            agency.contact = formdata.contact
            agency.mobile = formdata.mobile
            agency.share_rate = formdata.share_rate
            agency.create_time = utils.get_currtime()
            agency.update_time = agency.create_time
            agency.agency_desc = formdata.agency_desc
            agency.sync_ver = tools.gen_sync_ver()
            operator = self.db.query(models.TrOperator).filter_by(operator_name=agency.operator_name).first()
            if formdata.operator_pass:
                operator.operator_pass = md5(formdata.operator_pass.encode()).hexdigest()
            operator.operator_desc = formdata.agency_name
            operator.operator_status = formdata.operator_status
            operator.sync_ver = tools.gen_sync_ver()
            self.db.query(models.TrOperatorNodes).filter_by(operator_name=operator.operator_name).delete()
            for node_id in kwargs.get('operator_nodes') or []:
                onode = models.TrOperatorNodes()
                onode.operator_name = formdata.operator_name
                onode.node_id = node_id
                onode.sync_ver = tools.gen_sync_ver()
                self.db.add(onode)

            self.db.query(models.TrOperatorProducts).filter_by(operator_name=operator.operator_name).delete()
            for product_id in kwargs.get('operator_products') or []:
                oproduct = models.TrOperatorProducts()
                oproduct.operator_name = formdata.operator_name
                oproduct.product_id = product_id
                oproduct.sync_ver = tools.gen_sync_ver()
                self.db.add(oproduct)

            self.db.query(models.TrOperatorRule).filter_by(operator_name=operator.operator_name).delete()
            for path in kwargs.get('rule_item') or []:
                item = permit.get_route(path)
                if not item:
                    continue
                rule = models.TrOperatorRule()
                rule.id = utils.get_uuid()
                rule.operator_name = operator.operator_name
                rule.rule_name = item['name']
                rule.rule_path = item['path']
                rule.rule_category = item['category']
                rule.sync_ver = tools.gen_sync_ver()
                self.db.add(rule)

            permit.unbind_opr(operator.operator_name)
            self.add_oplog(u'更新代理商 %s' % utils.safeunicode(agency.agency_name))
            self.db.commit()
            for rule in self.db.query(models.TrOperatorRule).filter_by(operator_name=operator.operator_name):
                permit.bind_opr(rule.operator_name, rule.rule_path)

            return agency
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='agency_update_error')
            self.last_error = u'代理商更新失败:%s' % utils.safeunicode(err)
            return False

    def delete(self, agency_id, **kwargs):
        try:
            agency = self.db.query(models.TrAgency).get(agency_id)
            if not agency:
                raise ValueError(u'代理商不存在')
            if self.db.query(models.TrCustomer).filter_by(agency_id=agency_id).count() > 0:
                return ValueError(u'代理商下有用户，不允许删除')
            opr = self.db.query(models.TrOperator).filter_by(operator_name=agency.operator_name).first()
            if opr:
                self.db.query(models.TrOperatorRule).filter_by(operator_name=opr.operator_name).delete()
                self.db.query(models.TrOperator).filter_by(id=opr.id).delete()
            self.db.query(models.TrAgency).filter_by(id=agency_id).delete()
            self.add_oplog(u'删除代理商%s信息' % utils.safeunicode(agency.agency_name))
            self.db.commit()
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOperatorRule.__tablename__, dict(operator_name=agency.operator_name)), async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOperator.__tablename__, dict(id=opr.id)), async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAgency.__tablename__, dict(id=agency_id)), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            logger.exception(err, tag='agency_delete_error')
            self.last_error = u'代理商删除失败:%s' % utils.safeunicode(err)
            return False