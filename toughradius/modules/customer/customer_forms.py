#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}
boolean = {0: u'否',
 1: u'是'}
user_state = {0: u'未激活',
 1: u'正常',
 2: u'停机',
 3: u'销户',
 4: u'到期'}
bind_state = {0: u'不绑定',
 1: u'绑定'}
billing_types = {1: u'开通账号立即计费',
 0: u'首次使用开始计费'}
pwd_types = {1: u'手工设置',
 0: u'随机密码'}
_btn_style = {'class': 'btn btn-sm btn-default'}

def customer_fast_open_form(nodes = [], products = [], agencies = []):
    form = btforms.Form(title=u'用户快速开户', action='/admin/customer/fastopen')
    items = form.inputs = []
    items.append(btforms.Dropdown('node_id', description=u'区域*', args=nodes, required='required', **input_style))
    items.append(btforms.Dropdown('area_id', description=u'社区*', args=[], required='required', **input_style))
    items.append(btforms.Hidden('realname', description=u'用户姓名*', **input_style))
    items.append(btforms.Hidden('idcard', rules.len_of(0, 18), description=u'证件号码*', **input_style))
    items.append(btforms.Hidden('mobile', rules.len_of(0, 11), description=u'用户手机号码*', **input_style))
    items.append(btforms.Hidden('address', rules.len_of(1, 255), description=u'用户地址', required='required', **input_style))
    items.append(btforms.Dropdown('product_id', args=products, description=u'资费*', required='required', **input_style))
    items.append(btforms.Textbox('account_number', description=u'用户账号*', required='required', **input_style))
    items.append(btforms.Textbox('password', description=u'认证密码*', required='required', **input_style))
    items.append(btforms.Button('button', type='button', onclick='reBuildAccount();', html=u'<b>生成账号密码</b>', **_btn_style))
    items.append(btforms.Hidden('ip_address', description=u'用户IP地址', **input_style))
    items.append(btforms.Hidden('agency_id', description=u'代理商', **input_style))
    items.append(btforms.Hidden('charge_code', description=u'收费项', **input_style))
    items.append(btforms.Textbox('months', description=u'月数(包月有效)', **input_style))
    items.append(btforms.Textbox('days', description=u'天数(包日有效)', **input_style))
    items.append(btforms.Textbox('giftdays', rules.is_number, description=u'赠送天数', help=u'包月资费，买断包月资费有效', value=0, required='required', **input_style))
    items.append(btforms.Textbox('giftflows', rules.is_number, description=u'赠送流量(G)', help=u'流量包月资费有效', value=0, required='required', **input_style))
    items.append(btforms.Textbox('fee_value', rules.is_rmb, description=u'缴费金额(套餐资费+收费项)*', required='required', **input_style))
    items.append(btforms.Textbox('expire_date', rules.is_date, description=u'过期日期*', readonly='readonly', **input_style))
    items.append(btforms.Dropdown('billing_type', args=billing_types.items(), description=u'计费开始时间', **input_style))
    items.append(btforms.Hidden('status', value=1, description=u'用户状态', **input_style))
    items.append(btforms.Hidden('builder_name', description=u'指派施工人员', **input_style))
    items.append(btforms.Hidden('customer_desc', description=u'备注信息', rows=4, **input_style))
    items.append(btforms.Hidden('account_rule', description=u'账号生成规则'))
    items.append(btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style))
    return form


def customer_batch_open_form(nodes = [], products = []):
    form = btforms.Form(title=u'用户批量开户', action='/admin/customer/batchopen')
    items = form.inputs = []
    items.append(btforms.Dropdown('node_id', description=u'区域*', args=nodes, required='required', **input_style))
    items.append(btforms.Dropdown('area_id', description=u'社区*', args=[], required='required', **input_style))
    items.append(btforms.Dropdown('product_id', args=products, description=u'资费*', required='required', **input_style))
    items.append(btforms.Dropdown('pwd_type', args=pwd_types.items(), description=u'密码类型', **input_style))
    items.append(btforms.Textbox('password', description=u'认证密码*', **input_style))
    items.append(btforms.Textbox('opennum', rules.is_number, description=u'数量(最大1000)*', required='required', **input_style))
    items.append(btforms.Textbox('user_prefix', rules.is_alphanum2(1, 10), description=u'账号前缀*', required='required', **input_style))
    items.append(btforms.Textbox('suffix_len', rules.is_number, description=u'序号长度*', required='required', **input_style))
    items.append(btforms.Textbox('start_num', rules.is_number, description=u'开始序号*', required='required', **input_style))
    items.append(btforms.Textbox('expire_date', rules.is_date, description=u'过期日期*', readonly='readonly', **input_style))
    items.append(btforms.Hidden('billing_type', args=billing_types.items(), description=u'计费开始时间', **input_style))
    items.append(btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style))
    return form


def customer_open_form(nodes = [], products = [], agencies = []):
    form = btforms.Form(title=u'用户正常开户', action='/admin/customer/open')
    items = form.inputs = []
    items.append(btforms.Dropdown('node_id', description=u'区域*', args=nodes, required='required', **input_style))
    items.append(btforms.Dropdown('area_id', description=u'社区*', args=[], required='required', **input_style))
    items.append(btforms.Textbox('realname', rules.len_of(1, 64), description=u'用户姓名*', required='required', **input_style))
    items.append(btforms.Textbox('idcard', rules.len_of(0, 18), description=u'证件号码*', **input_style))
    items.append(btforms.Textbox('mobile', rules.len_of(0, 11), description=u'用户手机号码*', **input_style))
    items.append(btforms.Textbox('email', description=u'电子邮箱*', **input_style))
    items.append(btforms.Textbox('address', rules.len_of(1, 255), description=u'用户地址', hr=True, required='required', **input_style))
    items.append(btforms.Textbox('account_number', description=u'用户账号*', required='required', **input_style))
    items.append(btforms.Textbox('password', description=u'认证密码*', required='required', **input_style))
    items.append(btforms.Button('button', type='button', onclick='reBuildAccount();', html=u'<b>生成账号密码</b>', **_btn_style))
    items.append(btforms.Textbox('ip_address', description=u'用户IP地址', **input_style))
    items.append(btforms.Dropdown('product_id', args=products, description=u'资费*', required='required', **input_style))
    items.append(btforms.Dropdown('agency_id', args=agencies, description=u'代理商', **input_style))
    items.append(btforms.Dropdown('charge_code', args=[], description=u'收费项', **input_style))
    items.append(btforms.Textbox('months', description=u'月数(包月有效)', **input_style))
    items.append(btforms.Textbox('days', description=u'天数(包日有效)', **input_style))
    items.append(btforms.Textbox('giftdays', rules.is_number, description=u'赠送天数', help=u'包月资费，买断包月资费有效', value=0, required='required', **input_style))
    items.append(btforms.Textbox('giftflows', rules.is_number, description=u'赠送流量(G)', help=u'流量包月资费有效', value=0, required='required', **input_style))
    items.append(btforms.Textbox('fee_value', rules.is_rmb, description=u'缴费金额(套餐资费+收费项)*', required='required', **input_style))
    items.append(btforms.Textbox('expire_date', rules.is_date, description=u'过期日期*', readonly='readonly', **input_style))
    items.append(btforms.Hidden('status', value=1, description=u'用户状态', **input_style))
    items.append(btforms.Dropdown('builder_name', args=[], description=u'指派施工人员', **input_style))
    items.append(btforms.Textarea('customer_desc', description=u'备注信息', rows=4, **input_style))
    items.append(btforms.Dropdown('billing_type', args=billing_types.items(), description=u'计费开始时间', **input_style))
    items.append(btforms.Hidden('account_rule', description=u'账号生成规则'))
    items.append(btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style))
    return form


def customer_import_form():
    return btforms.Form(btforms.File('import_file', description=u'用户数据文件', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>立即导入</b>', **button_style), title=u'用户数据导入', action='/admin/customer/import')


customer_import_vform = dataform.Form(dataform.Item('realname', rules.not_null, description=u'用户姓名'), dataform.Item('account_number', rules.not_null, description=u'用户账号'), dataform.Item('password', rules.not_null, description=u'用户密码'), dataform.Item('node', rules.not_null, description=u'用户区域名'), dataform.Item('area', rules.not_null, description=u'用户社区名'), dataform.Item('product', rules.not_null, description=u'用户资费名称'), dataform.Item('idcard', rules.len_of(0, 32), description=u'证件号码'), dataform.Item('mobile', rules.len_of(0, 32), description=u'用户手机号码'), dataform.Item('address', description=u'用户地址'), dataform.Item('begin_date', rules.is_date, description=u'开通日期'), dataform.Item('expire_date', rules.is_date, description=u'过期日期'), dataform.Item('balance', rules.is_rmb, description=u'用户余额'), dataform.Item('time_length', description=u'用户时长'), dataform.Item('flow_length', description=u'用户流量'), title='import')

def customer_update_form(nodes = []):
    return btforms.Form(btforms.Hidden('account_number', description=u'用户账号'), btforms.Dropdown('node_id', description=u'区域*', args=nodes, required='required', **input_style), btforms.Dropdown('area_id', description=u'社区*', args=[], required='required', **input_style), btforms.Hidden('customer_id', description=u'mid', required='required', **input_style), btforms.Textbox('realname', rules.len_of(1, 64), description=u'用户姓名', required='required', **input_style), btforms.Hidden('customer_name', description=u'自助服务用户名', readonly='readonly', autocomplete='off', **input_style), btforms.Hidden('new_password', rules.len_of(0, 128), value='', description=u'自助服务密码(留空不修改)', **input_style), btforms.Textbox('email', rules.len_of(0, 128), description=u'电子邮箱', **input_style), btforms.Textbox('idcard', rules.len_of(0, 32), description=u'证件号码', **input_style), btforms.Textbox('mobile', rules.len_of(0, 32), description=u'用户手机号码', **input_style), btforms.Textbox('address', description=u'用户地址', hr=True, **input_style), btforms.Textarea('customer_desc', description=u'用户描述', rows=4, **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'用户基本信息修改', action='/admin/customer/update')


def customer_order_check_form():
    return btforms.Form(btforms.Textbox('order_id', description=u'订单号', readonly='readonly', **input_style), btforms.Textbox('order_fee', rules.is_rmb, description=u'订购交易金额', readonly='readonly', **input_style), btforms.Textbox('actual_fee', rules.is_rmb, description=u'订购实缴金额', required='required', **input_style), btforms.Textbox('audit_desc', rules.not_null, description=u'审核描述', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>确认审核</b>', **button_style), title=u'交易审核', action='/admin/customer/order/check')