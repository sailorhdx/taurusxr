#!/usr/bin/env python
# coding=utf-8
import os
from taurusxradius.taurusxlib import btforms, logger
from taurusxradius.taurusxlib.btforms import rules
from taurusxradius.taurusxlib.btforms.rules import button_style, input_style
from taurusxradius.modules.settings import *

forgot_button_style = {'class': 'btn btn-primary btn-block btn-lg'}
lg_input_style = {'class': 'form-control input-lg'}

def resetpassword_form(uuid='', token=''):
    form = btforms.Form(title=u'重置密码', id="resetpassword", action='/usrportal/resetpassword', glyphicon='1')
    items = form.inputs = []
    items.append(btforms.Hidden('uuid', value=str(uuid), description=u'uuid', required='required', **lg_input_style))
    items.append(btforms.Hidden('token', value=str(token), description=u'token', required='required', **lg_input_style))
    items.append(btforms.Password('password', glyphicon='glyphicon-lock', description=u'登录密码', required='required', **lg_input_style))
    items.append(btforms.Password('confirmpassword', glyphicon='glyphicon-lock', description=u'确认密码', required='required', **lg_input_style))
    items.append(btforms.Button('submit', type='submit', html=u'重置密码', **forgot_button_style))
    return form