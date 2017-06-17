#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}
account_rule_add_form = btforms.Form(btforms.Textbox('rule_name', rules.not_null, description=u'规则名称', required='required', **input_style), btforms.Textbox('user_prefix', rules.not_null, description=u'账号前缀', required='required', **input_style), btforms.Textbox('user_suffix_len', rules.is_number, description=u'账号后缀长度', value=6, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'新增账号生成规则', htopic='node', action='/admin/account_rule/add')
account_rule_update_form = btforms.Form(btforms.Hidden('id', description=u'规则ID'), btforms.Textbox('rule_name', rules.not_null, description=u'规则名称', required='required', **input_style), btforms.Textbox('user_prefix', rules.not_null, description=u'账号前缀', required='required', **input_style), btforms.Textbox('user_suffix_len', rules.is_number, description=u'账号后缀长度', value=6, readonly='readonly', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'修改账号生成规则', htopic='node', action='/admin/account_rule/update')