#!/usr/bin/env python
# coding=utf-8
import datetime
import time
import base64
from hashlib import md5
from toughradius.modules.ssportal.base import BaseHandler
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils, logger
from toughradius.modules import models

@permit.route('/acforward')

class AcForwardHandler(BaseHandler):
    """
    http://182.254.146.116:1819/acforward?action=new&user=
    
    http://182.254.146.116:1819/acforward?
    user=test
    &ip=192.168.2.91
    &timestemp=1484018336
    &action=renew
    &sign=803238d4b472d474d3dcd7db09ea90ec
     // sign = md5(user+ip+timestemp+action+share_secret)
    """

    def get(self):
        action = self.get_argument('action', '')
        acip = self.get_argument('acip', '')
        ip = self.get_argument('ip', '')
        temp_acurl = self.get_argument('url', '')
        dest_acip = ''
        dest_ip = ''
        try:
            if acip:
                dest_acip = base64.b64decode(acip)
                self.session['temp_acip'] = dest_acip
            if ip:
                dest_ip = base64.b64decode(ip)
                self.session['temp_userip'] = dest_ip
            else:
                dest_ip = self.request.remote_ip
                self.session['temp_userip'] = dest_ip
            self.session['temp_acurl'] = temp_acurl
            self.session.save()
            if action == 'new':
                self.redirect('/ssportal/product')
                return
            if action == 'renew':
                user = self.get_argument('user')
                timestemp = self.get_argument('timestemp')
                action = self.get_argument('action')
                sign = self.get_argument('sign')
                nas = self.db.query(models.TrBas).filter_by(ip_addr=dest_acip).first()
                if not nas:
                    logger.error('nas {0} not exists'.format(dest_acip), username=user)
                    self.redirect('/ssportal')
                    return
                signstr = user + ip + timestemp + action + str(nas.bas_secret) + acip
                logger.info(signstr)
                _sign = md5(signstr).hexdigest()
                logger.info('sign = ' + _sign)
                if sign != _sign:
                    logger.error('ssportal forward sign error', username=user)
                    self.redirect('/ssportal')
                    return
                account = self.db.query(models.TrAccount).get(user)
                if not account:
                    logger.error('ssportal forward error, account {0} not exists'.format(user), username=user)
                    self.redirect('/ssportal')
                    return
                self.set_session_user(account.customer_id, account.account_number, ip, utils.get_currtime())
                self.redirect('/ssportal/account')
        except Exception as err:
            logger.exception(err)
            self.redirect('/ssportal')