#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style

def bind_form():
    return btforms.Form(btforms.Hidden('openid', description=u'openid'), btforms.Textbox('username', rules.len_of(1, 32), description=u'账号名称', required='required', **input_style), btforms.Password('password', rules.len_of(1, 32), description=u'账号密码', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>绑定</b>', **button_style), title=u'用户微信绑定', action='')