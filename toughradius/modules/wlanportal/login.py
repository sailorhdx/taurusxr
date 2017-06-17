#!/usr/bin/env python
# coding=utf-8
import struct
import time
from twisted.internet import defer
from toughradius.toughlib import utils, logger, dispatch
from toughradius.toughlib.permit import permit
from toughradius.modules.wlanportal.base import BaseHandler
from toughradius.txportal import client
from toughradius.modules import models
import functools

@permit.route('/login')

class PortalLoginHandler(BaseHandler):
    """ portal 认证处理
    """

    @defer.inlineCallbacks
    def get(self):
        qstr = self.request.query
        username, password = self.get_remember_user()
        if username and password:
            yield self.post(qstr=qstr, username=username, password=password)
        else:
            wlan_params = self.get_wlan_params(qstr)
            ssid = wlan_params.get('ssid', 'default')
            if self.settings.debug:
                logger.info(u'Open portal auth page, wlan params:{0}'.format(utils.safeunicode(wlan_params)))
            tpl = self.get_template_attrs(ssid)
            if not tpl:
                tpl = {'page_title': u'无线认证',
                 'tpl_path': 'default'}
            tplpath = self.get_login_template(tpl['tpl_path'])
            self.render(tplpath, msg=None, tpl=tpl, qstr=qstr, **wlan_params)
        return

    @defer.inlineCallbacks
    def post(self, **kwargs):
        qstr = self.get_argument('qstr', '')
        username = self.get_argument('username', None)
        password = self.get_argument('password', None)
        if 'qstr' in kwargs:
            qstr = kwargs['qstr']
        if 'username' in kwargs:
            username = kwargs['username']
        if 'password' in kwargs:
            password = kwargs['password']
        wlan_params = self.get_wlan_params(qstr)
        logger.info(u'post wlan params:{0}'.format(utils.safeunicode(wlan_params)))
        ssid = wlan_params.get('ssid', 'default')
        wlanacip = wlan_params.get('wlanacip', '127.0.0.1')
        nasid = wlan_params.get('nasid', 'default')
        wlanuserip = wlan_params.get('wlanuserip', self.request.remote_ip)
        is_chap = self.settings.config.portal.chap in (1, '1', 'chap')
        userIp = wlanuserip
        start_time = time.time()
        nas = self.get_nas(wlanacip, nasid=nasid)
        if not nas:
            self.render_error(msg=u'AC设备地址或ID {0},{1} 未在本系统注册 '.format(wlanacip, nasid))
            return
        else:
            ac_addr = nas['ip_addr']
            ac_port = int(nas['ac_port'])
            secret = utils.safestr(nas['bas_secret'])
            _vendor = utils.safestr(nas['portal_vendor'])
            if _vendor not in ('cmccv1', 'cmccv2', 'huaweiv1', 'huaweiv2'):
                logger.error(nas)
                self.render_error(msg=u'AC设备 portal_vendor {0} 不支持 '.format(_vendor))
                return
            hm_mac = wlan_params.get('wlanstamac', '').replace('.', ':').replace('-', ':')
            macbstr = hm_mac and struct.pack('BBBBBB', *[ int(i, base=16) for i in hm_mac.split(':') ]) or None
            send_portal = functools.partial(client.send, secret, log=logger, debug=self.settings.debug, vendor=_vendor, timeout=5)
            vendor = client.PortalClient.vendors.get(_vendor)
            if self.settings.debug:
                logger.info(u'开始 [username:%s] Portal认证, 参数:%s' % (username, utils.safeunicode(wlan_params)))
            tpl = self.get_template_attrs(ssid)
            firsturl = tpl.get('home_page', '/navigate')

            def back_login(msg = u''):
                self.render(self.get_login_template(tpl['tpl_path']), tpl=tpl, msg=msg, qstr=qstr, **wlan_params)

            if not username:
                back_login(msg=u'用户名不能为空')
                return
            try:
                challenge_resp = None
                if is_chap:
                    challenge_req = vendor.proto.newReqChallenge(userIp, secret, mac=macbstr, chap=is_chap)
                    challenge_resp = yield send_portal(data=challenge_req, host=ac_addr, port=ac_port)
                    if challenge_resp.errCode > 0:
                        if challenge_resp.errCode == 2:
                            self.set_remerber_user(username, password)
                            self.redirect(firsturl)
                            return
                        raise Exception(vendor.mod.AckChallengeErrs[challenge_resp.errCode])
                if challenge_resp:
                    auth_req = vendor.proto.newReqAuth(userIp, username, password, challenge_resp.reqId, challenge_resp.get_challenge(), secret, ac_addr, serialNo=challenge_req.serialNo, mac=macbstr, chap=is_chap)
                else:
                    auth_req = vendor.proto.newReqAuth(userIp, username, password, 0, None, secret, ac_addr, chap=is_chap)
                auth_resp = yield send_portal(data=auth_req, host=ac_addr, port=ac_port)
                if auth_resp.errCode > 0:
                    if auth_resp.errCode == 2:
                        self.set_remerber_user(username, password)
                        self.redirect(firsturl)
                        return
                    text_info = auth_resp.get_text_info()
                    _err_msg = u'{0},{1}'.format(vendor.mod.AckAuthErrs[auth_resp.errCode], utils.safeunicode(text_info and text_info[0] or ''))
                    raise Exception(_err_msg)
                affack_req = vendor.proto.newAffAckAuth(userIp, secret, ac_addr, auth_req.serialNo, auth_resp.reqId, mac=macbstr, chap=is_chap)
                send_portal(data=affack_req, host=ac_addr, port=ac_port, noresp=True)
                logger.info(u'用户 [username:{0}] 认证成功'.format(username))
                if self.settings.debug:
                    logger.debug(u'用户 [username:%s] 认证耗时 [cast:%s ms]' % (username, (time.time() - start_time) * 1000))
                self.set_remerber_user(username, password)
                self.redirect(firsturl)
            except Exception as err:
                import traceback
                traceback.print_exc()
                back_login(msg=u'用户认证失败,%s' % utils.safeunicode(err.message))

            return


@permit.route('/')

class PortalIndexHandler(PortalLoginHandler):
    pass