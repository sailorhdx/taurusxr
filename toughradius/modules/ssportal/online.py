#!/usr/bin/env python
# coding=utf-8
import datetime
import time
from toughradius.modules.ssportal.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.toughlib import utils
from toughradius.modules.settings import *
from twisted.internet import defer
from toughradius.toughlib import logger, dispatch
from toughradius.txradius import authorize
from toughradius.txradius.radius import dictionary
import toughradius

@permit.route('/ssportal/online')

class OnlineHandler(BaseHandler):

    @authenticated
    def get(self):
        account_number = self.current_user.username
        onlines = self.db.query(models.TrOnline).filter_by(account_number=account_number)
        return self.render('online.html', onlines=onlines)


@permit.route('/ssportal/online/unlock')

class OnlineUnlockHandler(BaseHandler):
    dictionary = None

    @defer.inlineCallbacks
    @authenticated
    def get(self):
        try:
            username = self.current_user.username
            nas_addr = self.get_argument('nas_addr', None)
            session_id = self.get_argument('session_id', None)
            nas = self.db.query(models.TrBas).filter_by(ip_addr=nas_addr).first()
            if not nas:
                self.render_json(code=1, msg=u'当前设备不支持')
                return
            online = self.db.query(models.TrOnline).filter_by(nas_addr=nas_addr, acct_session_id=session_id).first()
            print nas_addr, session_id, online
            if not online:
                self.render_json(code=1, msg=u'在线用户不存在')
                return
            if not OnlineUnlockHandler.dictionary:
                OnlineUnlockHandler.dictionary = dictionary.Dictionary(os.path.join(os.path.dirname(toughradius.__file__), 'dictionarys/dictionary'))
            dm_params = dict(Framed_IP_Address=online.framed_ipaddr, User_Name=username, Acct_Session_Id=session_id)
            if int(self.get_param_value('radius_coa_send_nasaddr', 0)):
                dm_params['NAS_IP_Address'] = nas.ip_addr
            radius_code = yield authorize.disconnect(int(nas.vendor_id or 0), OnlineUnlockHandler.dictionary, nas.bas_secret, nas.ip_addr, coa_port=int(nas.coa_port or 3799), debug=True, **dm_params)
            if int(radius_code) == 44:
                self.render_json(code=0, msg=u'用户下线请求处理成功')
            else:
                self.render_json(code=1, msg=u'用户下线请求处理失败')
        except Exception as err:
            logger.exception(err)
            self.render_json(code=1, msg=u'用户下线失败，请联系客服')

        return