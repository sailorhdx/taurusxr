#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}
tpl_types = {'open': u'开户',
 'next': u'续费',
 'change': u'变更',
 'charge': u'充值',
 'cancel': u'销户'}
print_tpl_add_form = btforms.Form(btforms.Textbox('tpl_name', rules.len_of(2, 128), description=u'模板名', required='required', **input_style), btforms.Dropdown('tpl_types', description=u'打印类型(多选)', args=tpl_types.items(), required='required', multiple='multiple', size=5, **input_style), btforms.Textarea('tpl_content', rules.not_null, description=u'模板内容', rows=14, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'创建票据模板', action='/admin/printtpl/add')
print_tpl_update_form = btforms.Form(btforms.Hidden('id', description=u'模板ID'), btforms.Textbox('tpl_name', rules.len_of(2, 128), description=u'模板名', **input_style), btforms.Dropdown('tpl_types', description=u'打印类型(多选)', args=tpl_types.items(), required='required', multiple='multiple', size=5, **input_style), btforms.Textarea('tpl_content', rules.not_null, description=u'模板内容', rows=14, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'修改票据模板', action='/admin/printtpl/update')