#!/usr/bin/env python
# coding=utf-8
from taurusxradius.taurusxlib import btforms

login_button_style = {'class': 'btn btn-success btn-block btn-lg'}
lg_input_style = {'class': 'form-control input-lg'}

def login_form():
    form = btforms.Form(title=u'用户登录', id="login", action='/usrportal/login', glyphicon='1')
    items = form.inputs = []
    items.append(btforms.Textbox('account_number', glyphicon='glyphicon-user', description=u'用户账号', required='required', **lg_input_style))
    items.append(btforms.Password('password', glyphicon='glyphicon-lock', description=u'登录密码', required='required', **lg_input_style))
    items.append(btforms.Button('submit', type='submit', html=u'立即登录', **login_button_style))
    return form