#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}
booleans = {'0': u'否',
 '1': u'是'}
wlan_tpls = {'default': u'默认模板'}

def domain_add_vform():
    return btforms.Form(btforms.Dropdown('tpl_name', wlan_tpls.items(), rules.not_null, description=u'Hotspot 模版', required='required', **input_style), btforms.Textbox('domain_code', rules.is_alphanum2(2, 16), description=u'认证域编码', required='required', **input_style), btforms.Textbox('domain_desc', rules.not_null, description=u'域描述', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'增加无线认证域', action='/admin/wlan/domain/add')


def domain_update_vform():
    return btforms.Form(btforms.Hidden('id', description=u'编号'), btforms.Dropdown('tpl_name', wlan_tpls.items(), rules.not_null, description=u'Hotspot 模版', required='required', **input_style), btforms.Textbox('domain_code', rules.not_null, readonly='readonly', description=u'认证域编码', required='required', **input_style), btforms.Textbox('domain_desc', rules.not_null, description=u'域描述', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'修改认证域', action='/admin/wlan/domain/update')


def domain_attr_form(products = []):
    return btforms.Form(btforms.Textbox('domain_code', description=u'域编码', readonly='readonly', **input_style), btforms.Textbox('tpl_name', description=u'模版名', readonly='readonly', **input_style), btforms.Textbox('page_title', description=u'模版页面标题', **input_style), btforms.Dropdown('wlan_product_id', args=products, description=u'热点自动注册资费', **input_style), btforms.Dropdown('pwd_auth_eanble', args=booleans.items(), description=u'启用密码认证', **input_style), btforms.Dropdown('sms_auth_eanble', args=booleans.items(), description=u'启用短信认证', **input_style), btforms.Dropdown('wechat_auth_eanble', args=booleans.items(), description=u'启用微信认证', **input_style), btforms.Dropdown('qq_auth_eanble', args=booleans.items(), description=u'启用QQ认证', **input_style), btforms.Dropdown('free_auth_eanble', args=booleans.items(), description=u'启用免费认证', **input_style), btforms.Textbox('ssportal_url', description=u'自助服务链接', **input_style), btforms.Textbox('qrcode_url', description=u'二维码地址', **input_style), btforms.Textbox('copyright_text', description=u'页脚版权声明', **input_style), btforms.Textbox('ad1_img_url', description=u'广告图片地址1', **input_style), btforms.Textbox('ad2_img_url', description=u'广告图片地址2', **input_style), btforms.Textbox('ad3_img_url', description=u'广告图片地址3', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新配置</b>', **button_style), title=u'认证域参数配置', action='/admin/wlan/domain/attr/update')


domain_ap_add_form = btforms.Form(btforms.Hidden('domain_code', description=u'域编码'), btforms.Textbox('guid', rules.not_null, description=u'接入点唯一标识', required='required', **input_style), btforms.Textbox('ssid', rules.not_null, description=u'接入点SSID', required='required', **input_style), btforms.Textbox('ap_desc', rules.not_null, description=u'接入点描述', required='required', **input_style), title=u'增加认证域接入点', action='/admin/wlan/domain/ap/add')