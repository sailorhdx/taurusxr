#!/usr/bin/env python
# coding=utf-8
from twisted.internet import reactor
from toughradius.toughlib import utils, dispatch, logger
from toughradius.txradius import statistics
from toughradius.modules import models
from sqlalchemy.orm import scoped_session, sessionmaker
from toughradius.modules.settings import *
from toughradius.toughlib import db_cache as cache
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.dbutils import make_db
from toughradius.txradius.radius import dictionary
from toughradius.modules.events.event_basic import BasicEvent
from toughradius.modules.radius import radius_acct_stop
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.modules.events.settings import CLEAR_ONLINE_EVENT
from toughradius.txradius import authorize
import toughradius
import decimal
import datetime
import os
import json

class RadiusEvents(BasicEvent):
    dictionary = dictionary.Dictionary(os.path.join(os.path.dirname(toughradius.__file__), 'dictionarys/dictionary'))

    def get_request(self, online):
        if not online:
            return None
        else:
            session_time = (datetime.datetime.now() - datetime.datetime.strptime(online.acct_start_time, '%Y-%m-%d %H:%M:%S')).total_seconds()
            return Storage(account_number=online.account_number, mac_addr=online.mac_addr, nas_addr=online.nas_addr, nas_port=0, service_type='2', framed_ipaddr=online.framed_ipaddr, framed_netmask='', nas_class='', session_timeout=0, calling_station_id=online.mac_addr, acct_status_type=STATUS_TYPE_STOP, acct_input_octets=0, acct_output_octets=0, acct_session_id=online.acct_session_id, acct_session_time=session_time, acct_input_packets=online.input_total * 1024, acct_output_packets=online.output_total * 1024, acct_terminate_cause=5, acct_input_gigawords=0, acct_output_gigawords=0, event_timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), nas_port_type='15', nas_port_id=online.nas_port_id)

    def onSendResp(self, resp, disconnect_req):
        try:
            with make_db(self.db) as db:
                if disconnect_req and db.query(models.TrOnline).filter_by(nas_addr=disconnect_req.nas_addr, acct_session_id=disconnect_req.acct_session_id).count() > 0:
                    radius_acct_stop.RadiusAcctStop(self.dbengine, self.mcache, self.aes, disconnect_req).acctounting()
                logger.info(u'系统触发用户强制下线成功: %s; OnlineInfo: %s ' % (str(resp), json.dumps(disconnect_req)), trace='event')
                logger.info(u'send disconnect ok! coa resp : %s' % resp)
        except Exception as err:
            logger.exception(err)

    def onSendError(self, err, disconnect_req):
        try:
            with make_db(self.db) as db:
                if disconnect_req and db.query(models.TrOnline).filter_by(nas_addr=disconnect_req.nas_addr, acct_session_id=disconnect_req.acct_session_id).count() > 0:
                    radius_acct_stop.RadiusAcctStop(self.dbengine, self.mcache, self.aes, disconnect_req).acctounting()
                logger.info(u'系统触发用户强制下线失败: %s; OnlineInfo: %s ' % (err.getErrorMessage(), json.dumps(disconnect_req)), trace='event')
                logger.error(u'send disconnect done! %s' % err.getErrorMessage())
        except Exception as err:
            logger.exception(err)

    def event_clear_online(self, account_number, nas_addr, acct_session_id):
        try:
            with make_db(self.db) as db:
                logger.info('event clear expire online [username:{0}] {1} {2}'.format(account_number, nas_addr, acct_session_id), username=account_number)
                nas = db.query(models.TrBas).filter_by(ip_addr=nas_addr).first()
                if nas_addr and not nas:
                    db.query(models.TrOnline).filter_by(nas_addr=nas_addr, acct_session_id=acct_session_id).delete()
                    db.commit()
                    dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOnline.__tablename__, dict(nas_addr=nas_addr, acct_session_id=acct_session_id)), async=True)
                    return
                online = db.query(models.TrOnline).filter_by(nas_addr=nas_addr, acct_session_id=acct_session_id).first()
                clear_req = self.get_request(online)
                radius_acct_stop.RadiusAcctStop(self.dbengine, self.mcache, self.aes, clear_req).acctounting()
                logger.info(u'系统触发用户过期清理成功: [username:%s] OnlineInfo: %s ' % (str(account_number), json.dumps(clear_req)), trace='event', username=account_number)
        except Exception as err:
            logger.exception(err)

    def event_unlock_online(self, account_number, nas_addr, acct_session_id):
        with make_db(self.db) as db:
            logger.info('event unlock online [username:{0}] {1} {2}'.format(account_number, nas_addr, acct_session_id), username=account_number)
            nas = db.query(models.TrBas).filter_by(ip_addr=nas_addr).first()
            if nas_addr and not nas:
                db.query(models.TrOnline).filter_by(nas_addr=nas_addr, acct_session_id=acct_session_id).delete()
                db.commit()
                dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOnline.__tablename__, dict(nas_addr=nas_addr, acct_session_id=session_id)), async=True)
                return
            online = db.query(models.TrOnline).filter_by(nas_addr=nas_addr, acct_session_id=acct_session_id).first()
            dm_params = dict(User_Name=account_number, Framed_IP_Address=online.framed_ipaddr, Acct_Session_Id=acct_session_id)
            if int(self.get_param_value('radius_coa_send_nasaddr', 0)):
                dm_params['NAS_IP_Address'] = nas.ip_addr
            deferd = authorize.disconnect(int(nas.vendor_id or 0), self.dictionary, nas.bas_secret, nas.ip_addr, coa_port=int(nas.coa_port or 3799), debug=True, **dm_params).addCallback(self.onSendResp, self.get_request(online)).addErrback(self.onSendError, self.get_request(online))
            logreq = u'nas_addr=%s;coa_port=%s; username=%s; session_id=%s' % (nas.ip_addr,
             int(nas.coa_port or 3799),
             account_number,
             acct_session_id)
            logger.info(u'%s - 系统触发用户强制下线请求: CoaRequest: %s ' % logreq, trace='event', username=account_number)

    def event_check_online(self, account_number):
        with make_db(self.db) as db:
            try:
                logger.info('event check online [username:{0}] '.format(account_number), username=account_number)
                onlines = db.query(models.TrOnline).filter_by(account_number=account_number)
                for online in onlines:
                    acct_start_time = datetime.datetime.strptime(online.acct_start_time, '%Y-%m-%d %H:%M:%S')
                    acct_session_time = online.billing_times
                    nowdate = datetime.datetime.now()
                    dt = nowdate - acct_start_time
                    online_times = dt.total_seconds()
                    max_interim_intelval = int(self.get_param_value('radius_acct_interim_intelval', 240))
                    if online_times - acct_session_time > max_interim_intelval + 30:
                        logger.info('online %s overtime, system auto clear this online' % online.account_number, username=account_number)
                        dispatch.pub(CLEAR_ONLINE_EVENT, online.account_number, online.nas_addr, online.acct_session_id, async=True)

            except Exception as err:
                logger.exception(err)


def __call__(dbengine = None, mcache = None, **kwargs):
    return RadiusEvents(dbengine=dbengine, mcache=mcache, **kwargs)