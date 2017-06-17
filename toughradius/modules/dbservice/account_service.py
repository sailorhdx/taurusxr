#!/usr/bin/env python
# coding=utf-8
import datetime
import traceback
from toughradius.modules.settings import *
from hashlib import md5
from toughradius.modules import models
from toughradius.common import tools
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.btforms import rules
from toughradius.toughlib import utils, dispatch, redis_cache, logger
from toughradius.modules.dbservice import BaseService
from toughradius.modules.dbservice import logparams
from toughradius.modules.events.settings import ACCOUNT_DELETE_EVENT
from toughradius.modules.events.settings import CACHE_DELETE_EVENT
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.modules.events import settings as evset

class AccountService(BaseService):

    @logparams
    def delete(self, account_number, **kwargs):
        """用户账号删除

        :param account_number:   用户账号
        :type account_number:    string
        """
        try:
            if not account_number:
                raise ValueError(u'账号不能为空')
            account = self.db.query(models.TrAccount).get(account_number)
            self.db.query(models.TrAcceptLog).filter_by(account_number=account.account_number).delete()
            self.db.query(models.TrAccountAttr).filter_by(account_number=account.account_number).delete()
            self.db.query(models.TrBilling).filter_by(account_number=account.account_number).delete()
            self.db.query(models.TrTicket).filter_by(account_number=account.account_number).delete()
            self.db.query(models.TrOnline).filter_by(account_number=account.account_number).delete()
            self.db.query(models.TrAccount).filter_by(account_number=account.account_number).delete()
            self.db.query(models.TrCustomerOrder).filter_by(account_number=account.account_number).delete()
            self.add_oplog(u'删除用户账号%s' % account.account_number)
            self.db.commit()
            dispatch.pub(ACCOUNT_DELETE_EVENT, account.account_number, async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAcceptLog.__tablename__, dict(account_number=account.account_number)), async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAccountAttr.__tablename__, dict(account_number=account.account_number)), async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrBilling.__tablename__, dict(account_number=account.account_number)), async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOnline.__tablename__, dict(account_number=account.account_number)), async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAccount.__tablename__, dict(account_number=account.account_number)), async=True)
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrCustomerOrder.__tablename__, dict(account_number=account.account_number)), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户删除失败:%s' % utils.safeunicode(err.message)
            logger.error(self.last_error, tag='account_delete_error', username=account_number)
            return False

    def password(self, formdata, **kwargs):
        """用户密码修改

        :param formdata:   密码修改参数表
        :type formdata:    dict
        
        formdata params:

        :param account_number:   用户账号
        :type account_number:    string
        :param password:    用户新密码
        :type password:     string
        """
        try:
            account_number = self.parse_arg(formdata, 'account_number', rule=rules.not_null)
            password = self.parse_arg(formdata, 'password', rule=rules.not_null)
            print password
            account = self.db.query(models.TrAccount).get(account_number)
            account.password = self.aes.encrypt(password)
            account.sync_ver = tools.gen_sync_ver()
            node_id = self.db.query(models.TrCustomer.node_id).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.account_number == account_number).scalar()
            self.add_oplog(u'修改用户%s密码 ' % account_number)
            self.db.commit()
            dispatch.pub(CACHE_DELETE_EVENT, account_cache_key(account_number), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户修改密码失败:%s' % utils.safeunicode(err.message)
            logger.error(self.last_error, tag='account_uppwd_error', username=formdata.get('account_number'))
            return False

    @logparams
    def pause(self, account_number, **kwargs):
        """用户账号停机

        :param account_number:   用户账号
        :type account_number:    string
        """
        try:
            if not account_number:
                raise ValueError(u'账号不能为空')
            account = self.db.query(models.TrAccount).get(account_number)
            if account.status != 1:
                raise ValueError(u'用户当前状态不允许停机')
            _datetime = utils.get_currtime()
            account.last_pause = _datetime
            account.status = 2
            account.sync_ver = tools.gen_sync_ver()
            accept_log = models.TrAcceptLog()
            accept_log.id = utils.get_uuid()
            accept_log.accept_type = 'pause'
            accept_log.accept_source = 'console'
            accept_log.accept_desc = u'用户停机：上网账号:%s' % account_number
            accept_log.account_number = account.account_number
            accept_log.accept_time = _datetime
            accept_log.operator_name = self.operator.username
            accept_log.stat_year = accept_log.accept_time[0:4]
            accept_log.stat_month = accept_log.accept_time[0:7]
            accept_log.stat_day = accept_log.accept_time[0:10]
            self.db.add(accept_log)
            self.db.commit()
            dispatch.pub(evset.ACCOUNT_PAUSE_EVENT, account.account_number, async=True)
            dispatch.pub(evset.CACHE_DELETE_EVENT, account_cache_key(account.account_number), async=True)
            for online in self.db.query(models.TrOnline).filter_by(account_number=account_number):
                dispatch.pub(evset.UNLOCK_ONLINE_EVENT, account_number, online.nas_addr, online.acct_session_id, async=True)

            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户停机失败:%s' % utils.safeunicode(err.message)
            logger.error(self.last_error, tag='account_pause_error', username=account_number)
            return False

    @logparams
    def resume(self, account_number, **kwargs):
        """用户账号复机

        :param account_number:   用户账号
        :type account_number:    string
        """
        try:
            if not account_number:
                raise ValueError(u'账号不能为空')
            account = self.db.query(models.TrAccount).get(account_number)
            node_id = self.db.query(models.TrCustomer.node_id).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.account_number == account_number).scalar()
            if account.status != 2:
                return self.render_json(code=1, msg=u'用户当前状态不允许复机')
            account.status = 1
            _datetime = datetime.datetime.now()
            _pause_time = datetime.datetime.strptime(account.last_pause, '%Y-%m-%d %H:%M:%S')
            _expire_date = datetime.datetime.strptime(account.expire_date + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            days = (_expire_date - _pause_time).days
            new_expire = (_datetime + datetime.timedelta(days=int(days))).strftime('%Y-%m-%d')
            account.expire_date = new_expire
            account.sync_ver = tools.gen_sync_ver()
            accept_log = models.TrAcceptLog()
            accept_log.id = utils.get_uuid()
            accept_log.accept_type = 'resume'
            accept_log.accept_source = 'console'
            accept_log.accept_desc = u'用户复机：上网账号:%s' % account_number
            accept_log.account_number = account.account_number
            accept_log.accept_time = utils.get_currtime()
            accept_log.operator_name = self.operator.username
            accept_log.stat_year = accept_log.accept_time[0:4]
            accept_log.stat_month = accept_log.accept_time[0:7]
            accept_log.stat_day = accept_log.accept_time[0:10]
            self.db.add(accept_log)
            self.db.commit()
            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户停机失败:%s' % utils.safeunicode(err.message)
            logger.error(self.last_error, tag='account_resume_error', username=account_number)
            return False

    @logparams
    def update(self, formdata, **kwargs):
        """用户账号策略修改

        :param formdata:   密码修改参数表
        :type formdata:    dict
        
        formdata params:
        
        :param account_number:   用户账号
        :type account_number:    string
        :param ip_address:    用户IP地址
        :type ip_address:     string - x.x.x.x
        :param install_address:    用户安装地址
        :type install_address:    string
        :param domain:    用户域，对BRAS的特定扩展
        :type domain:    string
        :param user_concur_number:   用户在线数限制
        :type user_concur_number:    int
        :param bind_mac:    用户是否绑定mac
        :type bind_mac:    int - 0 不绑定 1 绑定
        :param bind_vlan:    用户是否绑定vlan
        :type bind_vlan:    int 0 不绑定 1 绑定
        :param account_desc:    用户描述
        :type account_desc:    string
        """
        try:
            account_number = self.parse_arg(formdata, 'account_number', rule=rules.not_null)
            user_concur_number = self.parse_arg(formdata, 'user_concur_number', rule=rules.is_number)
            bind_mac = self.parse_arg(formdata, 'bind_mac', rule=rules.is_number)
            bind_vlan = self.parse_arg(formdata, 'bind_vlan', rule=rules.is_number)
            ip_address = self.parse_arg(formdata, 'ip_address')
            install_address = self.parse_arg(formdata, 'install_address')
            domain = self.parse_arg(formdata, 'domain')
            account_desc = self.parse_arg(formdata, 'account_desc')
            account = self.db.query(models.TrAccount).get(account_number)
            node_id = self.db.query(models.TrCustomer.node_id).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.account_number == account_number).scalar()
            if ip_address is not None:
                account.ip_address = ip_address
            if install_address is not None:
                account.install_address = install_address
            account.user_concur_number = user_concur_number
            account.bind_mac = bind_mac
            account.bind_vlan = bind_vlan
            if domain is not None:
                account.domain = domain
            if account_desc is not None:
                account.account_desc = account_desc
            account.sync_ver = tools.gen_sync_ver()
            self.add_oplog(u'修改上网账号信息:%s' % account.account_number)
            self.db.commit()
            dispatch.pub(CACHE_DELETE_EVENT, account_cache_key(account.account_number), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户修改失败:%s' % utils.safeunicode(err.message)
            logger.error(self.last_error, tag='account_update_error', username=formdata.get('account_number'))
            return False

        return

    @logparams
    def release(self, account_number, **kwargs):
        """用户账号复机

        :param account_number:   用户账号
        :type account_number:    string
        """
        try:
            if not account_number:
                raise ValueError(u'账号不能为空')
            account = self.db.query(models.TrAccount).get(account_number)
            node_id = self.db.query(models.TrCustomer.node_id).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.account_number == account_number).scalar()
            account.mac_addr = ''
            account.vlan_id1 = 0
            account.vlan_id2 = 0
            account.sync_ver = tools.gen_sync_ver()
            self.add_oplog(u'释放用户账号（%s）绑定信息' % account_number)
            self.db.commit()
            dispatch.pub(CACHE_DELETE_EVENT, account_cache_key(account.account_number), async=True)
            return True
        except Exception as err:
            self.db.rollback()
            self.last_error = u'用户解绑失败:%s' % utils.safeunicode(err)
            logger.error(self.last_error, tag='account_release_error', username=account_number)
            return False