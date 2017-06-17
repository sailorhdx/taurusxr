#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style

def password_form():
    return btforms.Form(btforms.Password('opassword', rules.not_null, iwidth=3, description=u'旧密码', required='required', **input_style), btforms.Password('npassword', rules.not_null, iwidth=3, description=u'新密码', required='required', **input_style), btforms.Password('cpassword', rules.not_null, iwidth=3, description=u'确认新密码', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>修改密码</b>', **button_style), title=u'修改密码', action='/ssportal/password/update')