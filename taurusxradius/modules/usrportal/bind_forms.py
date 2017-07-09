#!/usr/bin/env python
# coding=utf-8
from taurusxradius.taurusxlib import btforms
from taurusxradius.taurusxlib.btforms import rules
from taurusxradius.taurusxlib.btforms.rules import button_style, input_style

lbutton_style = {'class': 'btn btn-sm btn-link'}

def bind_email_form(email=''):
    return btforms.Form(
        btforms.Textbox('email', rules.is_email, value=email, description=u'电子邮箱', required='required', **input_style),
        btforms.Button('submit', type='submit', html=u'<b>立即绑定</b>', **button_style),
        title=u'绑定邮箱',
        action='/usrportal/bind/email')


def bind_mobile_form(mobile=''):
    return btforms.Form(
        btforms.Textbox('mobile', value=mobile, description=u'用户手机号', required='required', **input_style),
        btforms.Textbox('vcode', description=u'验证码', required='required', **input_style),
        btforms.Button('smsvcode', id='smsvcode', type='button', html=u'<b>发送短信验证码</b>', onclick='send_vcode()', **lbutton_style),
        btforms.Button('submit', type='submit', html=u'<b>立即绑定</b>', **button_style),
        title=u'绑定手机',
        action='/usrportal/bind/mobile')