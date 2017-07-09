#!/usr/bin/env python
# coding=utf-8

from taurusxradius.taurusxlib import btforms
from taurusxradius.taurusxlib.btforms import rules
from taurusxradius.taurusxlib.btforms.rules import input_style

lbutton_style = {'class': 'btn btn-sm btn-link'}
register_button_style = {'class': 'btn btn-danger btn-block btn-lg'}
lg_input_style = {'class': 'form-control input-lg'}

def register_form(is_smsvcode=0, is_email=0):
    form = btforms.Form(title=u'用户注册', id="register", action='/usrportal/register', glyphicon='1')
    items = form.inputs = []
    if is_smsvcode: #开启短信验证，使用手机号作为ID
        items.append(btforms.Textbox('mobile', rules.is_telephone, glyphicon='glyphicon-phone', description=u'用户手机号', required='required', **lg_input_style))
        items.append(btforms.Textbox('vcode', glyphicon='glyphicon-pushpin', description=u'验证码', required='required', **lg_input_style))
        items.append(btforms.Button('smsvcode', id='smsvcode', type='button', html=u'<b>发送短信验证码</b>', onclick='send_vcode()', **lbutton_style))
    elif is_email: #开启邮件验证，使用邮箱地址作为ID
        items.append(btforms.Textbox('email', rules.is_email, glyphicon='glyphicon-envelope', description=u'电子邮箱', required='required', **lg_input_style))
    else: # 否则用户自定义ID
        items.append(btforms.Textbox('account_number', glyphicon='glyphicon-user', description=u'用户账号',required='required', **lg_input_style))
    items.append(btforms.Password('password', glyphicon='glyphicon-lock', description=u'登录密码', required='required', **lg_input_style))
    items.append(btforms.Password('confirmpassword', glyphicon='glyphicon-lock', description=u'确认密码', required='required', qualTo='#password', **lg_input_style))
    items.append(btforms.Button('submit', type='submit', html=u'立即注册', **register_button_style))
    return form

def register_customer_open_form():
    form = btforms.Form(title=u'用户注册开户')
    items = form.inputs = []
    items.append(btforms.Textbox('node_id', description=u'区域*', required='required', **input_style))
    items.append(btforms.Textbox('area_id', description=u'社区*', required='required', **input_style))
    items.append(btforms.Textbox('realname', rules.len_of(1, 64), description=u'用户姓名*', required='required', **input_style))
    items.append(btforms.Textbox('idcard', rules.len_of(0, 18), description=u'证件号码*', **input_style))
    items.append(btforms.Textbox('mobile', rules.len_of(0, 11), description=u'用户手机号码*', **input_style))
    items.append(btforms.Textbox('email', description=u'电子邮箱*', **input_style))
    items.append(btforms.Textbox('address', rules.len_of(1, 255), description=u'用户地址', hr=True, **input_style))
    items.append(btforms.Textbox('account_number', description=u'用户账号*', required='required', **input_style))
    items.append(btforms.Textbox('password', description=u'认证密码*', required='required', **input_style))
    items.append(btforms.Textbox('ip_address', description=u'用户IP地址', **input_style))
    items.append(btforms.Textbox('product_id', description=u'资费*', required='required', **input_style))
    items.append(btforms.Textbox('agency_id', description=u'代理商', **input_style))
    items.append(btforms.Textbox('charge_code', description=u'收费项', **input_style))
    items.append(btforms.Textbox('months', description=u'月数(包月有效)', **input_style))
    items.append(btforms.Textbox('days', description=u'天数(包日有效)', **input_style))
    items.append(btforms.Textbox('giftdays', rules.is_number, description=u'赠送天数', help=u'包月资费，买断包月资费有效', value=0, required='required', **input_style))
    items.append(btforms.Textbox('giftflows', rules.is_number, description=u'赠送流量(G)', help=u'流量包月资费有效', value=0, required='required', **input_style))
    items.append(btforms.Textbox('fee_value', rules.is_rmb, description=u'缴费金额(套餐资费+收费项)*', required='required', **input_style))
    items.append(btforms.Textbox('expire_date', rules.is_date, description=u'过期日期*', readonly='readonly', **input_style))
    items.append(btforms.Hidden('status', value=1, description=u'用户状态', **input_style))
    items.append(btforms.Textbox('builder_name', description=u'指派施工人员', **input_style))
    items.append(btforms.Textarea('customer_desc', description=u'备注信息', rows=4, **input_style))
    items.append(btforms.Textbox('billing_type', description=u'计费开始时间', **input_style))
    items.append(btforms.Hidden('account_rule', description=u'账号生成规则'))
    return form