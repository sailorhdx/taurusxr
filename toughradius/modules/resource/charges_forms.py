#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}
charge_add_form = btforms.Form(btforms.Textbox('charge_code', rules.not_null, description=u'收费项编码', required='required', **input_style), btforms.Textbox('charge_name', rules.not_null, description=u'收费项名称', required='required', **input_style), btforms.Textbox('charge_value', rules.is_rmb, description=u'收费项金额(元)', required='required', **input_style), btforms.Textbox('charge_desc', rules.not_null, description=u'收费项描述', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'新增收费项', action='/admin/charge/add')
charge_update_form = btforms.Form(btforms.Textbox('charge_code', rules.not_null, description=u'收费项编码', readonly='readonly', **input_style), btforms.Textbox('charge_name', rules.not_null, description=u'收费项名称', required='required', **input_style), btforms.Textbox('charge_value', rules.is_rmb, description=u'收费项金额(元)', required='required', **input_style), btforms.Textbox('charge_desc', rules.not_null, description=u'收费项描述', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'修改收费项', action='/admin/charge/update')