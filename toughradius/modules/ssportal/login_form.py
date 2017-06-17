#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style

def login_form():
    return btforms.Form(btforms.Textbox('username', rules.not_null, iwidth=3, description=u'认证账号', required='required', **input_style), btforms.Password('password', rules.not_null, iwidth=3, description=u'账号密码', required='required', **input_style), btforms.Hidden('next', description=u'next url'), btforms.Button('submit', type='submit', html=u'<b>登 陆</b>', **button_style), title=u'用户登陆', action='/ssportal/login')