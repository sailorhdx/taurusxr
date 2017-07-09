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