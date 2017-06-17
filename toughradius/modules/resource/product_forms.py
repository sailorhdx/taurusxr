#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
from toughradius.modules.settings import *
button_style = {'class': 'btn btn-sm bg-navy'}
boolean = {0: u'否',
 1: u'是'}
product_policy = {PPMonth: u'预付费包月',
 APMonth: u'后付费包月',
 BOMonth: u'买断包月',
 BOTimes: u'买断时长',
 BOFlows: u'买断流量',
 PPDay: u'预付费包日',
 BODay: u'买断包日'}
product_status_dict = {0: u'正常',
 1: u'停用'}
attrtype_dict = {0: u'普通属性',
 1: u'Radius 属性'}
attr_types = {'flow_price': u'流量充值单价(元/G)',
 'month_price': u'按月续费单价(元/月)',
 'day_price': u'按天续费单价(元/天)',
 'max_giftflows': u'最大赠送流量值(G)',
 'max_giftdays': u'最大赠送天数',
 'product_tag': u'资费充值卡标签',
 'Framed-Pool': u'[RADIUS] 用户地址池'}

def product_add_form(policy = 0, charges = [], pools = []):
    _policy = int(policy)
    form = btforms.Form(title=u'创建资费', action='/admin/product/add')
    form.inputs = []
    additem = form.inputs.append
    additem(btforms.Textbox('product_id', rules.is_alphanum2(4, 32), description=u'资费编码', required='required', **input_style))
    additem(btforms.Textbox('product_name', rules.len_of(4, 64), description=u'资费名称', required='required', **input_style))
    additem(btforms.Dropdown('ispub', args=boolean.items(), description=u'是否发布到自助订购套餐', **input_style))
    additem(btforms.Hidden('product_policy', value=policy, description=u''))
    if _policy == PPMonth:
        form.desc = u'预付费包月：以每月单价为基础，用户可自由订购多月，到期即停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'每月单价(元)', required='required', **input_style))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
    elif _policy == APMonth:
        form.desc = u'后付费包月：以每月单价为基础，先使用，下个月初期生成使用账单'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'每月单价(元)', required='required', **input_style))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
    elif _policy == BOMonth:
        form.desc = u'买断包月：以月为单位进行套餐打包(如包季度，半年，一年等)，设定买断总价，用户一次性订购，到期即停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'买断包月总价(元)', required='required', **input_style))
        additem(btforms.Textbox('fee_months', rules.is_number, description=u'买断授权月数', value=0, **input_style))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
    elif _policy == BOTimes:
        form.desc = u'买断时长：一次性将固定的时长打包为套餐，提供用户一次性订购，在使用过程中实时扣除时间，扣完为止。(设备必须支持实时记帐)，剩余时长为零时停止服务'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'买断时长总价(元)', required='required', **input_style))
        additem(btforms.Textbox('fee_times', rules.is_number3, description=u'买断时长(小时)', value=0, **input_style))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
    elif _policy == BOFlows:
        form.desc = u'买断流量：一次性将固定的流量打包为套餐，提供用户一次性订购，在使用过程中实时扣除流量，扣完为止。(设备必须支持实时记帐)，剩余流量为零时停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'买断流量总价(元)', required='required', **input_style))
        additem(btforms.Textbox('fee_flows', rules.is_number3, description=u'买断流量(G)', value=0, **input_style))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
    elif _policy == PPDay:
        form.desc = u'预付费包日：以每日单价为基础，用户可自由订购多日，到期即停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'每日单价(元)', required='required', **input_style))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
    elif _policy == BODay:
        form.desc = u'买断包日：以日为单位进行套餐打包(任意天数)，设定买断总价，用户一次性订购，到期即停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'买断包日总价(元)', required='required', **input_style))
        additem(btforms.Textbox('fee_days', rules.is_number3, description=u'买断授权天数', value=0, **input_style))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
    additem(btforms.Dropdown('product_charges', description=u'关联收费项(多选)', args=charges, multiple='multiple', size=6, **input_style))
    additem(btforms.Dropdown('addr_pool', args=pools, description=u'地址池', **input_style))
    additem(btforms.Textbox('concur_number', rules.is_numberOboveZore, description=u'同时在线数(0表示不限制)', value='0', **input_style))
    additem(btforms.Dropdown('bind_mac', args=boolean.items(), description=u'是否绑定MAC ', **input_style))
    additem(btforms.Dropdown('bind_vlan', args=boolean.items(), description=u'是否绑定VLAN ', **input_style))
    additem(btforms.Textbox('input_max_limit', rules.is_number3, description=u'最大上行速率(Mbps)', required='required', **input_style))
    additem(btforms.Textbox('output_max_limit', rules.is_number3, description=u'最大下行速率(Mbps)', required='required', **input_style))
    additem(btforms.Dropdown('free_auth', args=boolean.items(), description=u'支持到期免费授权', **input_style))
    additem(btforms.Textbox('free_auth_uprate', rules.is_number3, description=u' 免费授权最大上行速率(Mbps)', **input_style))
    additem(btforms.Textbox('free_auth_downrate', rules.is_number3, description=u'免费授权最大下行速率(Mbps)', **input_style))
    additem(btforms.Button('submit', type='submit', id='submit', html=u'<b>提交</b>', **button_style))
    return form


def product_update_form(policy = 0, charges = [], pools = []):
    _policy = int(policy)
    form = btforms.Form(title=u'创建资费', action='/admin/product/update')
    form.inputs = []
    additem = form.inputs.append
    additem(btforms.Textbox('id', description=u'资费编码', readonly='readonly', **input_style))
    additem(btforms.Textbox('product_name', rules.len_of(4, 64), description=u'资费名称', required='required', **input_style))
    additem(btforms.Textbox('product_policy_name', description=u'资费策略', readonly='readonly', **input_style))
    additem(btforms.Dropdown('ispub', args=boolean.items(), description=u'是否发布到自助订购套餐', **input_style))
    additem(btforms.Hidden('product_policy', value=policy, description=u''))
    if _policy == PPMonth:
        form.desc = u'预付费包月：以每月单价为基础，用户可自由订购多月，到期即停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'每月单价(元)', required='required', **input_style))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
    elif _policy == APMonth:
        form.desc = u'后付费包月：以每月单价为基础，先使用，下个月初期生成使用账单'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'每月单价(元)', required='required', **input_style))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
    elif _policy == BOMonth:
        form.desc = u'买断包月：以月为单位进行套餐打包(如包季度，半年，一年等)，设定买断总价，用户一次性订购，到期即停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'买断包月总价(元)', required='required', **input_style))
        additem(btforms.Textbox('fee_months', rules.is_number, description=u'买断授权月数', value=0, **input_style))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
    elif _policy == BOTimes:
        form.desc = u'买断时长：一次性将固定的时长打包为套餐，提供用户一次性订购，在使用过程中实时扣除时间，扣完为止。(设备必须支持实时记帐)，剩余时长为零时停止服务'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'买断时长总价(元)', required='required', **input_style))
        additem(btforms.Textbox('fee_times', rules.is_number3, description=u'买断时长(小时)', value=0, **input_style))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
    elif _policy == BOFlows:
        form.desc = u'买断流量：一次性将固定的流量打包为套餐，提供用户一次性订购，在使用过程中实时扣除流量，扣完为止。(设备必须支持实时记帐)，剩余流量为零时停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'买断流量总价(元)', required='required', **input_style))
        additem(btforms.Textbox('fee_flows', rules.is_number3, description=u'买断流量(G)', value=0, **input_style))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
    elif _policy == PPDay:
        form.desc = u'预付费包日：以每日单价为基础，用户可自由订购多日，到期即停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'每日单价(元)', required='required', **input_style))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_days', value=0, description=u'买断授权天数'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
    elif _policy == BODay:
        form.desc = u'买断包日：以日为单位进行套餐打包(任意天数)，设定买断总价，用户一次性订购，到期即停止服务。'
        additem(btforms.Textbox('fee_price', rules.is_rmb, description=u'买断包日总价(元)', required='required', **input_style))
        additem(btforms.Textbox('fee_days', rules.is_number3, description=u'买断授权天数', value=0, **input_style))
        additem(btforms.Hidden('fee_flows', value=0, description=u'买断流量(G)'))
        additem(btforms.Hidden('fee_times', value=0, description=u'买断时长(小时)'))
        additem(btforms.Hidden('fee_months', value=0, description=u'买断授权月数'))
    additem(btforms.Dropdown('addr_pool', args=pools, description=u'地址池', **input_style))
    additem(btforms.Dropdown('product_status', args=product_status_dict.items(), description=u'资费状态', required='required', **input_style))
    additem(btforms.Dropdown('product_charges', description=u'关联收费项(多选)', args=charges, multiple='multiple', size=6, **input_style))
    additem(btforms.Textbox('concur_number', rules.is_numberOboveZore, description=u'同时在线数(0表示不限制)', value='0', **input_style))
    additem(btforms.Dropdown('bind_mac', args=boolean.items(), description=u'是否绑定MAC ', **input_style))
    additem(btforms.Dropdown('bind_vlan', args=boolean.items(), description=u'是否绑定VLAN ', **input_style))
    additem(btforms.Textbox('input_max_limit', rules.is_number3, description=u'最大上行速率(Mbps)', required='required', **input_style))
    additem(btforms.Textbox('output_max_limit', rules.is_number3, description=u'最大下行速率(Mbps)', required='required', **input_style))
    additem(btforms.Dropdown('free_auth', args=boolean.items(), description=u'支持到期免费授权', **input_style))
    additem(btforms.Textbox('free_auth_uprate', rules.is_number3, description=u' 免费授权最大上行速率(Mbps)', **input_style))
    additem(btforms.Textbox('free_auth_downrate', rules.is_number3, description=u'免费授权最大下行速率(Mbps)', **input_style))
    additem(btforms.Button('submit', type='submit', id='submit', html=u'<b>提交</b>', **button_style))
    return form


product_attr_add_form = btforms.Form(btforms.Hidden('product_id', description=u'资费编号'), btforms.Dropdown('attr_type', args=attrtype_dict.items(), description=u'属性类型', required='required', **input_style), btforms.Dropdown('attr_types', args=attr_types.items(), description=u'预定义属性', required='required', **input_style), btforms.Textbox('attr_name', rules.len_of(1, 255), description=u'属性名称', required='required', help=u'属性参考', **input_style), btforms.Textbox('attr_value', rules.len_of(1, 255), description=u'属性值', required='required', **input_style), btforms.Textbox('attr_desc', rules.len_of(1, 255), description=u'属性描述', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'创建资费属性', action='/admin/product/attr/add')
product_attr_update_form = btforms.Form(btforms.Hidden('id', description=u'编号'), btforms.Hidden('product_id', description=u'资费编号'), btforms.Dropdown('attr_type', args=attrtype_dict.items(), description=u'属性类型', required='required', **input_style), btforms.Dropdown('attr_types', args=attr_types.items(), description=u'预定义属性', required='required', **input_style), btforms.Textbox('attr_name', rules.len_of(1, 255), description=u'属性名称', readonly='required', **input_style), btforms.Textbox('attr_value', rules.len_of(1, 255), description=u'属性值', required='required', **input_style), btforms.Textbox('attr_desc', rules.len_of(1, 255), description=u'属性描述', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'修改资费属性', action='/admin/product/attr/update')