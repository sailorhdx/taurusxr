#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}
boolean = {0: u'否',
 1: u'是'}
cardtype = {'product': u'资费卡',
 'balance': u'余额卡',
 'flowlen': u'流量卡',
 'timelen': u'时长卡'}
pwdtype = {'random': u'随机密码'}
cardstatus = {0: u'初始化',
 1: u'已激活',
 2: u'已使用'}

def vcard_batch_form():
    return btforms.Form(btforms.Dropdown('card_type', description=u'卡类型', args=cardtype.items(), required='required', **input_style), btforms.Dropdown('card_pwdtype', description=u'卡密码类型', args=pwdtype.items(), required='required', **input_style), btforms.Textbox('product_tag', rules.is_alphanum2(0, 32), description=u'资费标签(资费卡)', **input_style), btforms.Textbox('expire_date', rules.is_date, description=u'过期时间', required='required', **input_style), btforms.Textbox('credit', rules.is_number, description=u'储值余额(余额卡|元)', default=0, **input_style), btforms.Textbox('flowlen', rules.is_number, description=u'储值流量(余额卡|G)', default=0, **input_style), btforms.Textbox('timelen', rules.is_number, description=u'储值时长(时长卡|小时)', default=0, **input_style), btforms.Textbox('fee_price', rules.is_number, description=u'零售价(元)', default=0, required='required', **input_style), btforms.Textbox('num', rules.is_number, description=u'发行数量(最大100)', default=10, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'发行充值卡', action='/admin/vcard/batchadd')
