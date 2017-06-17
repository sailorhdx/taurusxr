#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import input_style
button_style = {'class': 'btn btn-sm'}
opr_status_dict = {0: u'正常',
 1: u'停用'}

def agency_add_form(nodes = [], products = []):
    return btforms.Form(btforms.Textbox('agency_name', rules.len_of(1, 255), description=u'代理商名称', **input_style), btforms.Textbox('contact', rules.not_null, description=u'联系人', **input_style), btforms.Textbox('mobile', rules.len_of(1, 255), description=u'手机号码', **input_style), btforms.Textbox('amount', rules.is_rmb, description=u'初始余额', **input_style), btforms.Textbox('share_rate', rules.is_number, description=u'分成比例(0-100)', **input_style), btforms.Textbox('operator_name', rules.len_of(2, 32), description=u'操作员名称', required='required', **input_style), btforms.Password('operator_pass', rules.len_of(6, 128), description=u'操作员密码', required='required', **input_style), btforms.Dropdown('operator_nodes', description=u'关联区域(多选)', args=nodes, required='required', multiple='multiple', size=4, **input_style), btforms.Dropdown('operator_products', description=u'关联资费(多选)', args=products, required='required', multiple='multiple', size=6, **input_style), btforms.Textarea('agency_desc', description=u'代理商描述', rows=2, **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'代理商开户', action='/admin/agency/add')


def agency_update_form(nodes = [], products = []):
    return btforms.Form(btforms.Hidden('agency_id', description=u'编号'), btforms.Textbox('agency_name', rules.len_of(1, 255), description=u'代理商名称', **input_style), btforms.Textbox('contact', rules.not_null, description=u'联系人', **input_style), btforms.Textbox('mobile', rules.len_of(1, 255), description=u'手机号码', **input_style), btforms.Textbox('share_rate', rules.is_number, description=u'分成比例(0-100)', **input_style), btforms.Textbox('operator_name', description=u'操作员名称', readonly='readonly', **input_style), btforms.Textbox('operator_desc', rules.len_of(0, 255), description=u'操作员姓名', **input_style), btforms.Password('operator_pass', rules.len_of(0, 128), description=u'操作员密码(留空不修改)', autocomplete='off', **input_style), btforms.Dropdown('operator_status', description=u'操作员状态', args=opr_status_dict.items(), required='required', **input_style), btforms.Dropdown('operator_nodes', description=u'关联区域(多选)', args=nodes, required='required', multiple='multiple', size=4, **input_style), btforms.Dropdown('operator_products', description=u'关联资费(多选)', args=products, required='required', multiple='multiple', size=6, **input_style), btforms.Textarea('agency_desc', description=u'代理商描述', rows=2, **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'代理商修改', action='/admin/agency/update')


def agency_recharge_form():
    return btforms.Form(btforms.Hidden('agency_id', description=u'编号'), btforms.Textbox('agency_name', rules.len_of(1, 255), description=u'代理商名称', readonly='readonly', **input_style), btforms.Textbox('fee_value', rules.is_rmb, description=u'充值金额', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'代理商充值', action='/admin/agency/recharge')