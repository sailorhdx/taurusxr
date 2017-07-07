#!/usr/bin/env python
# coding=utf-8
import os
from taurusxradius.taurusxlib import btforms, logger
from taurusxradius.taurusxlib.btforms import rules
from taurusxradius.taurusxlib.btforms.rules import button_style, input_style
from taurusxradius.modules.settings import *
lbutton_style = {'class': 'btn btn-sm btn-link'}
register_button_style = {'class': 'btn btn-danger btn-block btn-lg'}
login_button_style = {'class': 'btn btn-success btn-block btn-lg'}
forgot_button_style = {'class': 'btn btn-primary btn-block btn-lg'}
lg_input_style = {'class': 'form-control input-lg'}
boolean = {0: u'否',
 1: u'是'}

def order_form(policy):
    form = btforms.Form(title=u'套餐订购', action='/usrportal/product/order')
    items = form.inputs = []
    items.append(btforms.Textbox('realname', rules.not_null, size=64, description=u'用户姓名', required='required', **input_style))
    items.append(btforms.Textbox('account_number', description=u'用户账号', readonly='readonly', **input_style))
    items.append(btforms.Textbox('email', description=u'电子邮箱', required='required', **input_style))
    items.append(btforms.Textbox('password', rules.is_alphanum2(6, 9), description=u'认证密码', required='required', **input_style))
    items.append(btforms.Textbox('product_name', readonly='readonly', description=u'资费', **input_style))
    items.append(btforms.Hidden('product_id', description=u'资费', required='required', **input_style))
    if int(policy) == PPMonth:
        items.append(btforms.Textbox('months', rules.is_number, description=u'订购月数(预付费包月)', required='required', **input_style))
    else:
        items.append(btforms.Hidden('months', description=u'订购月数(预付费包月)', **input_style))
    if int(policy) == PPDay:
        items.append(btforms.Textbox('days', rules.is_number, description=u'订购天数(预付费包天)', required='required', **input_style))
    else:
        items.append(btforms.Hidden('days', description=u'订购天数(预付费包天)', **input_style))
    if os.environ.get('LICENSE_TYPE') != 'community':
        items.append(btforms.Textbox('vcard_code', description=u'充值卡', **input_style))
        items.append(btforms.Password('vcard_pwd', description=u'充值卡密码', **input_style))
    items.append(btforms.Button('submit', type='submit', html=u'<b>提交订单</b>', **button_style))
    return form


def smsvcode_form(pid = '', phone = ''):
    form = btforms.Form(title=u'套餐订购', action='/usrportal/product/order')
    items = form.inputs = []
    items.append(btforms.Hidden('product_id', description=u'资费', value=pid, required='required', **input_style))
    items.append(btforms.Textbox('account_number', description=u'用户手机号', value=phone, required='required', **input_style))
    items.append(btforms.Textbox('vcode', description=u'验证码', required='required', **input_style))
    items.append(btforms.Button('smsvcode', id='smsvcode', type='button', html=u'<b>发送短信验证码</b>', onclick='send_vcode()', **lbutton_style))
    items.append(btforms.Button('submit', type='submit', html=u'<b>下一步</b>', **button_style))
    return form


def renew_form(policy, get_product_attr_val):
    if not policy is not None:
        raise AssertionError
    form = btforms.Form(title=u'套餐续费', action='/usrportal/product/renew')
    items = form.inputs = []
    items.append(btforms.Textbox('account_number', description=u'用户账号', readonly='readonly', **input_style))
    items.append(btforms.Textbox('product_name', readonly='readonly', description=u'资费', **input_style))
    items.append(btforms.Hidden('product_id', description=u'资费', required='required', **input_style))
    if int(policy) == PPMonth:
        items.append(btforms.Textbox('months', rules.is_number, description=u'续费月数', required='required', **input_style))
    elif int(policy) == BOMonth:
        items.append(btforms.Textbox('months', rules.is_number, description=u'续费月数(填0表示续费整个套餐)', value='0', required='required', **input_style))
    else:
        items.append(btforms.Hidden('months', description=u'订购月数(预付费包月)', **input_style))
    if int(policy) == PPDay:
        items.append(btforms.Textbox('days', rules.is_number, description=u'续费天数', required='required', **input_style))
    elif int(policy) == BODay:
        items.append(btforms.Textbox('days', rules.is_number, description=u'续费天数(填0表示续费整个套餐)', value='0', required='required', **input_style))
    else:
        items.append(btforms.Hidden('days', description=u'订购天数(预付费包天)', **input_style))
    """
        如果套餐未设置product_tag标签扩展属性则，不支持充值卡充值
        发行充值卡时，设置资费标签，以便与套餐进行绑定
        为套餐设置的充值卡，选择“资费卡”类型，并设置零售价格即可
    """
    if os.environ.get('LICENSE_TYPE') != 'community' and get_product_attr_val('product_tag'):
        items.append(btforms.Textbox('vcard_code', description=u'充值卡', **input_style))
        items.append(btforms.Password('vcard_pwd', description=u'充值卡密码', **input_style))
    return form

def profile_order_form(policy, get_product_attr_val):
    form = btforms.Form(title=u'套餐订购', action='/usrportal/product/reneworder')
    items = form.inputs = []
    items.append(btforms.Textbox('account_number', description=u'用户账号', readonly='readonly', **input_style))
    items.append(btforms.Textbox('product_name', readonly='readonly', description=u'资费', **input_style))
    items.append(btforms.Hidden('product_id', description=u'资费', required='required', **input_style))
    if int(policy) == PPMonth:
        items.append(btforms.Textbox('months', rules.is_number, description=u'订购月数(预付费包月)', required='required', **input_style))
    else:
        items.append(btforms.Hidden('months', description=u'订购月数(预付费包月)', **input_style))
    if int(policy) == PPDay:
        items.append(btforms.Textbox('days', rules.is_number, description=u'订购天数(预付费包天)', required='required', **input_style))
    else:
        items.append(btforms.Hidden('days', description=u'订购天数(预付费包天)', **input_style))

    if os.environ.get('LICENSE_TYPE') != 'community' and get_product_attr_val('product_tag'):
        items.append(btforms.Textbox('vcard_code', description=u'充值卡', **input_style))
        items.append(btforms.Password('vcard_pwd', description=u'充值卡密码', **input_style))
    items.append(btforms.Button('submit', type='submit', html=u'<b>提交订单</b>', **button_style))
    return form

def charge_form():
    form = btforms.Form(title=u'账号充值', action='/usrportal/product/charge')
    items = form.inputs = []
    items.append(btforms.Textbox('account_number', description=u'用户账号', readonly='readonly', **input_style))
    items.append(btforms.Textbox('product_name', readonly='readonly', description=u'资费', **input_style))
    items.append(btforms.Hidden('product_id', description=u'资费', required='required', **input_style))
    items.append(btforms.Textbox('fee_value', rules.is_rmb, description=u'充值金额(元)', required='required', **input_style))
    return form


def vcard_charge_form():
    form = btforms.Form(title=u'充值卡充值', action='/usrportal/product/vcardcharge')
    items = form.inputs = []
    items.append(btforms.Textbox('account_number', description=u'用户账号', readonly='readonly', **input_style))
    items.append(btforms.Textbox('product_name', readonly='readonly', description=u'资费', **input_style))
    items.append(btforms.Hidden('product_id', description=u'资费', required='required', **input_style))
    items.append(btforms.Textbox('vcard_code', rules.not_null, description=u'充值卡', required='required', **input_style))
    items.append(btforms.Password('vcard_pwd', rules.not_null, description=u'充值卡密码', required='required', **input_style))
    return form

def login_form():
    form = btforms.Form(title=u'用户登录', id="login", action='/usrportal/login', glyphicon='1')
    items = form.inputs = []
    items.append(btforms.Textbox('account_number', glyphicon='glyphicon-user', description=u'用户账号', required='required', **lg_input_style))
    items.append(btforms.Password('password', glyphicon='glyphicon-lock', description=u'登录密码', required='required', **lg_input_style))
    items.append(btforms.Button('submit', type='submit', html=u'立即登录', **login_button_style))
    return form

def register_form(is_smsvcode=0, is_email=0):
    form = btforms.Form(title=u'用户注册', id="register", action='/usrportal/register', glyphicon='1')
    items = form.inputs = []
    if is_smsvcode: #开启短信验证，使用手机号作为ID
        items.append(btforms.Textbox('mobile', glyphicon='glyphicon-phone', description=u'用户手机号', required='required', **lg_input_style))
        items.append(btforms.Textbox('vcode', glyphicon='glyphicon-pushpin', description=u'验证码', required='required', **lg_input_style))
        items.append(btforms.Button('smsvcode', id='smsvcode', type='button', html=u'<b>发送短信验证码</b>', onclick='send_vcode()', **lbutton_style))
    elif is_email: #开启邮件验证，使用邮箱地址作为ID
        items.append(btforms.Textbox('email', glyphicon='glyphicon-envelope', description=u'电子邮箱', required='required', **lg_input_style))
    else: # 否则用户自定义ID
        items.append(btforms.Textbox('account_number', glyphicon='glyphicon-user', description=u'用户账号',required='required', **lg_input_style))
    items.append(btforms.Password('password', glyphicon='glyphicon-lock', description=u'登录密码', required='required', **lg_input_style))
    items.append(btforms.Password('confirmpassword', glyphicon='glyphicon-lock', description=u'确认密码', required='required', qualTo='#password', **lg_input_style))
    items.append(btforms.Button('submit', type='submit', html=u'立即注册', **register_button_style))
    return form

def forgot_form(is_smsvcode, is_email):
    form = btforms.Form(title=u'找回密码', id="forgot", action='/usrportal/forgot', glyphicon='1')
    items = form.inputs = []
    if is_smsvcode:
        items.append(btforms.Textbox('mobile', glyphicon='glyphicon-phone', description=u'用户手机号', required='required', **lg_input_style))
        items.append(btforms.Textbox('vcode', glyphicon='glyphicon-pushpin', description=u'验证码', required='required', **lg_input_style))
        items.append(btforms.Button('smsvcode', id='smsvcode', type='button', html=u'<b>发送短信验证码</b>', onclick='send_vcode()', **lbutton_style))
    elif is_email:
        items.append(btforms.Textbox('email', glyphicon='glyphicon-envelope', description=u'电子邮箱', required='required', **lg_input_style))
    if is_smsvcode or is_email:
        items.append(btforms.Button('submit', type='submit', html=u'找回密码', **forgot_button_style))

    return form

def resetpassword_form(is_smsvcode=0, is_email=0, uuid='', token='', account_number='', mobile='', email=''):
    form = btforms.Form(title=u'重置密码', id="resetpassword", action='/usrportal/resetpassword', glyphicon='1')
    items = form.inputs = []
    if is_smsvcode:
        items.append(btforms.Textbox('mobile', glyphicon='glyphicon-phone', value=mobile, description=u'用户手机号', readonly='readonly', required='required', **lg_input_style))
    elif is_email:
        items.append(btforms.Textbox('email', glyphicon='glyphicon-envelope', value=email, description=u'电子邮箱', readonly='readonly', required='required', **lg_input_style))
    if is_smsvcode or is_email:
        items.append(btforms.Hidden('uuid', value=str(uuid), description=u'uuid', required='required', **lg_input_style))
        items.append(btforms.Hidden('token', value=str(token), description=u'token', required='required', **lg_input_style))
        items.append(btforms.Password('password', glyphicon='glyphicon-lock', description=u'登录密码', required='required', **lg_input_style))
        items.append(btforms.Password('confirmpassword', glyphicon='glyphicon-lock', description=u'确认密码', required='required', **lg_input_style))
        items.append(btforms.Button('submit', type='submit', html=u'重置密码', **forgot_button_style))
    return form