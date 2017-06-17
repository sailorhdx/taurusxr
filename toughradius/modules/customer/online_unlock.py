#!/usr/bin/env python
# coding=utf-8
import os
import json
import cyclone.web
import datetime
from toughradius.modules import models
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.toughlib import logger, dispatch
from toughradius.toughlib.storage import Storage
from toughradius.modules.radius import radius_acct_stop
from toughradius.modules.settings import *
from toughradius.modules.events.settings import DBSYNC_STATUS_ADD
from toughradius.txradius import authorize
from toughradius.txradius.radius import dictionary
import toughradius

@permit.route('/admin/customer/online/unlock', u'用户在线解锁', MenuUser, order=4.0001)

class CustomerOnlineUnlockHandler(BaseHandler):
    dictionary = None

    def get_request(self, online):
        session_time = (datetime.datetime.now() - datetime.datetime.strptime(online.acct_start_time, '%Y-%m-%d %H:%M:%S')).total_seconds()
        return Storage(account_number=online.account_number, mac_addr=online.mac_addr, nas_addr=online.nas_addr, nas_port=0, service_type=0, framed_ipaddr=online.framed_ipaddr, framed_netmask='', nas_class='', session_timeout=0, calling_station_id='00:00:00:00:00:00', acct_status_type=STATUS_TYPE_STOP, acct_input_octets=0, acct_output_octets=0, acct_session_id=online.acct_session_id, acct_session_time=session_time, acct_input_packets=0, acct_output_packets=0, acct_terminate_cause=5, acct_input_gigawords=0, acct_output_gigawords=0, event_timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), nas_port_type='0', nas_port_id=online.nas_port_id)

    def onSendResp(self, resp, disconnect_req):
        if self.db.query(models.TrOnline).filter_by(nas_addr=disconnect_req.nas_addr, acct_session_id=disconnect_req.acct_session_id).count() > 0:
            radius_acct_stop.RadiusAcctStop(self.application.db_engine, self.application.mcache, self.application.aes, disconnect_req).acctounting()
        logger.info(u'人工触发用户强制下线成功: %s; OnlineInfo: %s ' % (str(resp), json.dumps(disconnect_req)), trace='event')
        self.render_json(code=0, msg=u'send disconnect ok! coa resp : %s' % resp)

    def onSendError(self, err, disconnect_req):
        if self.db.query(models.TrOnline).filter_by(nas_addr=disconnect_req.nas_addr, acct_session_id=disconnect_req.acct_session_id).count() > 0:
            radius_acct_stop.RadiusAcctStop(self.application.db_engine, self.application.mcache, self.application.aes, disconnect_req).acctounting()
        logger.info(u'人工触发用户强制下线解锁失败: %s; OnlineInfo: %s ' % (err.getErrorMessage(), json.dumps(disconnect_req)), trace='event')
        self.render_json(code=0, msg=u'send disconnect done! %s' % err.getErrorMessage())

    @authenticated
    def get(self):
        self.post()

    @authenticated
    def post(self):
        username = self.get_argument('username', None)
        nas_addr = self.get_argument('nas_addr', None)
        session_id = self.get_argument('session_id', None)
        nas = self.db.query(models.TrBas).filter_by(ip_addr=nas_addr).first()
        if nas_addr and not nas:
            self.db.query(models.TrOnline).filter_by(nas_addr=nas_addr, acct_session_id=session_id).delete()
            self.db.commit()
            dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOnline.__tablename__, dict(nas_addr=nas_addr, acct_session_id=session_id)), async=True)
            self.render_json(code=1, msg=u'nasaddr not exists, online clear!')
            return
        elif nas_addr and not session_id:
            onlines = self.db.query(models.TrOnline).filter_by(nas_addr=nas_addr)
            for online in onlines:
                radius_acct_stop.RadiusAcctStop(self.application.db_engine, self.application.mcache, self.application.aes, self.get_request(online)).acctounting()

            self.render_json(code=1, msg=u'unlock all online done!')
            return
        else:
            online = self.db.query(models.TrOnline).filter_by(nas_addr=nas_addr, acct_session_id=session_id).first()
            if not online:
                self.render_json(code=1, msg=u'online not exists')
                return
            if not CustomerOnlineUnlockHandler.dictionary:
                CustomerOnlineUnlockHandler.dictionary = dictionary.Dictionary(os.path.join(os.path.dirname(toughradius.__file__), 'dictionarys/dictionary'))
            dm_params = dict(Framed_IP_Address=online.framed_ipaddr, User_Name=username, Acct_Session_Id=session_id)
            if int(self.get_param_value('radius_coa_send_nasaddr', 0)):
                dm_params['NAS_IP_Address'] = nas.ip_addr
            deferd = authorize.disconnect(int(nas.vendor_id or 0), CustomerOnlineUnlockHandler.dictionary, nas.bas_secret, nas.ip_addr, coa_port=int(nas.coa_port or 3799), debug=True, **dm_params)
            deferd.addCallback(self.onSendResp, self.get_request(online)).addErrback(self.onSendError, self.get_request(online))
            logreq = u'nas_addr=%s;coa_port=%s; username=%s; session_id=%s' % (nas.ip_addr,
             int(nas.coa_port or 3799),
             username,
             session_id)
            logger.info(u'人工触发用户强制下线请求: CoaRequest: %s ' % logreq, trace='event', username=username)
            return deferd