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

def forgot_step1_form():
    form = btforms.Form(title=u'找回密码', id="forgot-step1", action='/usrportal/forgot/step1', glyphicon='1')
    items = form.inputs = []
    items.append(btforms.Textbox('userid', glyphicon='glyphicon-user', description=u'帐号绑定的邮箱或手机号码', required='required', **lg_input_style))
    items.append(btforms.Button('submit', type='submit', html=u'验证信息', **forgot_button_style))

    return form

def forgot_mobile_form():
    form = btforms.Form(title=u'找回密码', id="forgot", action='/usrportal/forgot/mobile', glyphicon='1')
    items = form.inputs = []
    items.append(btforms.Textbox('mobile', glyphicon='glyphicon-phone', description=u'用户手机号', required='required', **lg_input_style))
    items.append(btforms.Textbox('vcode', glyphicon='glyphicon-pushpin', description=u'验证码', required='required', **lg_input_style))
    items.append(btforms.Button('smsvcode', id='smsvcode', type='button', html=u'<b>发送短信验证码</b>', onclick='send_vcode()', **lbutton_style))
    items.append(btforms.Button('submit', type='submit', html=u'找回密码', **forgot_button_style))

    return form

def forgot_email_form():
    form = btforms.Form(title=u'找回密码', id="forgot", action='/usrportal/forgot/email', glyphicon='1')
    items = form.inputs = []
    items.append(btforms.Textbox('email', glyphicon='glyphicon-envelope', description=u'电子邮箱', required='required', **lg_input_style))
    items.append(btforms.Button('submit', type='submit', html=u'找回密码', **forgot_button_style))

    return form

def forgot_form(is_smsvcode=0, is_email=0):
    form = btforms.Form(title=u'找回密码', id="forgot", action='/usrportal/forgot', glyphicon='1')
    items = form.inputs = []
    if is_smsvcode:
        items.append(btforms.Hidden('mode', value=0, description=u'短信找回', required='required', **lg_input_style))
        items.append(btforms.Textbox('mobile', glyphicon='glyphicon-phone', description=u'用户手机号', required='required', **lg_input_style))
        items.append(btforms.Textbox('vcode', glyphicon='glyphicon-pushpin', description=u'验证码', required='required', **lg_input_style))
        items.append(btforms.Button('smsvcode', id='smsvcode', type='button', html=u'<b>发送短信验证码</b>', onclick='send_vcode()', **lbutton_style))
    elif is_email:
        items.append(btforms.Hidden('mode', value=1, description=u'邮箱找回', required='required', **lg_input_style))
        items.append(btforms.Textbox('email', glyphicon='glyphicon-envelope', description=u'电子邮箱', required='required', **lg_input_style))
    if is_smsvcode or is_email:
        items.append(btforms.Button('submit', type='submit', html=u'找回密码', **forgot_button_style))

    return form
