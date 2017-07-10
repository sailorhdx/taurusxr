#!/usr/bin/env python
# coding=utf-8
import os
from taurusxradius.taurusxlib import btforms, logger
from taurusxradius.taurusxlib.btforms import rules
from taurusxradius.taurusxlib.btforms.rules import button_style, input_style
from taurusxradius.modules.settings import *
lbutton_style = {'class': 'btn btn-sm btn-link'}
forgot_button_style = {'class': 'btn btn-primary btn-block btn-lg'}
lg_input_style = {'class': 'form-control input-lg'}

def forgot_mobile_form():
    form = btforms.Form(title=u'找回密码', id="forgot", action='/usrportal/forgot/mobile', glyphicon='1')
    items = form.inputs = []
    items.append(btforms.Textbox('mobile', rules.is_telephone, glyphicon='glyphicon-phone', description=u'用户手机号', required='required', **lg_input_style))
    items.append(btforms.Textbox('vcode', glyphicon='glyphicon-pushpin', description=u'验证码', required='required', **lg_input_style))
    items.append(btforms.Button('smsvcode', id='smsvcode', type='button', html=u'<b>发送短信验证码</b>', onclick='send_vcode()', **lbutton_style))
    items.append(btforms.Button('submit', type='submit', html=u'找回密码', **forgot_button_style))

    return form

def forgot_email_form():
    form = btforms.Form(title=u'找回密码', id="forgot", action='/usrportal/forgot/email', glyphicon='1')
    items = form.inputs = []
    items.append(btforms.Textbox('email', rules.is_email, glyphicon='glyphicon-envelope', description=u'电子邮箱', required='required', **lg_input_style))
    items.append(btforms.Button('submit', type='submit', html=u'找回密码', **forgot_button_style))

    return form