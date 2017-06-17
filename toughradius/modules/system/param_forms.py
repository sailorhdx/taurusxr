#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
import os
button_style = {'class': 'btn btn-sm bg-navy'}
boolean = {0: u'否',
 1: u'是'}
booleans = {'0': u'否',
 '1': u'是'}
fee_precisions = {'yuan': u'元',
 'fen': u'分'}
bool_bypass = {'0': u'免密码认证',
 '1': u'强制密码认证',
 '2': u'免用户密码认证'}
renew_time_types = {'0': u'从当前时间开始计算',
 '1': u'从用户到期时间开始计算'}
themes = {'skin-black': u'黑色风格',
          'skin-blue': u'蓝色风格',
          'skin-green': u'绿色风格',
          'skin-purple': u'紫色风格',
          'skin-red': u'红色风格',
          'skin-yellow': u'黄色风格'}
en_modes = {'normal': u'明文',
 'compatible': u'兼容模式',
 'safe': u'安全模式'}
if not os.environ.get('DEMO_VER'):
    sys_form = btforms.Form(btforms.Textbox('system_name', description=u'管理系统名称', help=u'管理系统名称,可以根据你的实际情况进行定制', **input_style), btforms.Dropdown('system_theme', args=themes.items(), description=u'系统风格样式', **input_style), btforms.Textbox('ssportal_title', description=u'网上营业厅名称', **input_style), btforms.Textbox('support_desc', description=u'技术服务支持声明', help=u'显示在管理登陆和网上营业厅页面底部', **input_style), btforms.Textbox('login_logo', description=u'登陆页面Logo(200x120)', **input_style), btforms.Textbox('login_bgimg', description=u'登陆页面背景图片(1920x600)', **input_style), btforms.Textbox('index_logo', description=u'管理页面Logo(191x36)', **input_style), btforms.Textbox('ssportal_banner_bg', description=u'网上营业厅背景图(1920x300+)', **input_style), btforms.Dropdown('style_nav_fixed', args=booleans.items(), description=u'设置顶部导航栏固定', help=u'顶部导航条固定样式，若需要在小屏幕设备管理，建议设置为否', **input_style), btforms.Dropdown('style_nav_busstat_link', args=booleans.items(), description=u'导航栏显示运营分析链接', **input_style), btforms.Dropdown('style_nav_status_link', args=booleans.items(), description=u'导航栏显示系统状态链接', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'管理界面设置', action='/admin/param/update?active=syscfg')
else:
    sys_form = btforms.Form(btforms.Textbox('system_name', description=u'管理系统名称', help=u'管理系统名称,可以根据你的实际情况进行定制', **input_style), btforms.Dropdown('system_theme', args=themes.items(), description=u'系统风格样式', **input_style), btforms.Textbox('ssportal_title', description=u'网上营业厅名称', readonly='readonly', **input_style), btforms.Textbox('support_desc', description=u'技术服务支持声明', help=u'显示在管理登陆和网上营业厅页面底部', readonly='readonly', **input_style), btforms.Textbox('login_logo', description=u'登陆页面Logo(200x120)', readonly='readonly', **input_style), btforms.Textbox('login_bgimg', description=u'登陆页面背景图片(1920x600)', readonly='readonly', **input_style), btforms.Textbox('index_logo', description=u'管理页面Logo(191x36)', readonly='readonly', **input_style), btforms.Textbox('ssportal_banner_bg', description=u'网上营业厅背景图(1920x300+)', readonly='readonly', **input_style), btforms.Dropdown('style_nav_fixed', args=booleans.items(), description=u'设置顶部导航栏固定', help=u'顶部导航条固定样式，若需要在小屏幕设备管理，建议设置为否', **input_style), btforms.Dropdown('style_nav_doc_link', args=booleans.items(), description=u'导航栏显示文档链接', **input_style), btforms.Dropdown('style_nav_busstat_link', args=booleans.items(), description=u'导航栏显示运营分析链接', **input_style), btforms.Dropdown('style_nav_status_link', args=booleans.items(), description=u'导航栏显示系统状态链接', **input_style), title=u'管理界面设置', action='/admin/param/update?active=syscfg')
if not os.environ.get('DEMO_VER'):
    mail_form = btforms.Form(btforms.Textbox('smtp_server', description=u'SMTP服务器', **input_style), btforms.Textbox('smtp_port', description=u'SMTP服务器端口', **input_style), btforms.Dropdown('smtp_tls', args=booleans.items(), description=u'SMTP启用TLS/SSL', **input_style), btforms.Textbox('smtp_from', description=u'SMTP邮件发送地址', **input_style), btforms.Textbox('smtp_user', description=u'SMTP用户名', **input_style), btforms.Password('smtp_pwd', description=u'SMTP密码', help=u'如果密码不是必须的，请填写none', **input_style), btforms.Dropdown('mail_notify_enable', args=booleans.items(), description=u'启动到期提醒', **input_style), btforms.Textbox('mail_notify_interval', rules.is_number, description=u'到期提醒间隔(分钟)', **input_style), btforms.Textbox('mail_notify_time', rules.is_time_hm, description=u'到期提醒时间(hh:mm)', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'邮件设置', action='/admin/param/update?active=mailcfg')
else:
    mail_form = btforms.Form(btforms.Textbox('smtp_server', description=u'SMTP服务器', **input_style), btforms.Dropdown('smtp_tls', args=booleans.items(), description=u'SMTP启用TLS/SSL', **input_style), btforms.Textbox('smtp_from', description=u'SMTP邮件发送地址', **input_style), btforms.Dropdown('mail_notify_enable', args=booleans.items(), description=u'启动到期提醒', **input_style), btforms.Textbox('mail_notify_interval', rules.is_number, description=u'到期提醒间隔(分钟)', **input_style), btforms.Textbox('mail_notify_time', rules.is_time_hm, description=u'到期提醒时间(hh:mm)', **input_style), title=u'邮件设置', action='/admin/param/update?active=mailcfg')
sms_gateway = {'smscn': u'云信(sms.cn)',
 'sendcloud': u'闪达短信(sendcloud)',
 'qcloud': u'腾讯云短信'}
if not os.environ.get('DEMO_VER'):
    sms_form = btforms.Form(btforms.Dropdown('sms_gateway', sms_gateway.items(), description=u'短信网关', **input_style), btforms.Textbox('sms_api_user', description=u'短信API用户或 apikey', **input_style), btforms.Password('sms_api_pwd', description=u'短信API密码或 apisecret', **input_style), btforms.Dropdown('sms_notify_enable', args=booleans.items(), description=u'启动到期提醒', **input_style), btforms.Textbox('sms_notify_interval', rules.is_number, description=u'到期提醒间隔(分钟)', **input_style), btforms.Textbox('sms_notify_time', rules.is_time_hm, description=u'到期提醒时间(hh:mm)', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'短信设置', action='/admin/param/update?active=smscfg')
else:
    sms_form = btforms.Form(btforms.Dropdown('sms_api_url', sms_gateway.items(), description=u'短信网关', **input_style), btforms.Dropdown('sms_notify_enable', args=booleans.items(), description=u'启动到期提醒', readonly='readonly', **input_style), btforms.Textbox('sms_notify_interval', rules.is_number, description=u'到期提醒间隔(分钟)', readonly='readonly', **input_style), btforms.Textbox('sms_notify_time', rules.is_time_hm, description=u'到期提醒时间(hh:mm)', readonly='readonly', **input_style), title=u'短信设置', action='/admin/param/update?active=smscfg')
if not os.environ.get('DEMO_VER'):
    rad_form = btforms.Form(btforms.Dropdown('radius_bypass', args=bool_bypass.items(), description=u'Radius认证模式', **input_style), btforms.Textbox('radius_acct_interim_intelval', rules.is_number, description=u'Radius记账间隔(秒)', help=u'radius向bas设备下发的全局记账间隔，bas不支持则不生效', **input_style), btforms.Textbox('radius_max_session_timeout', rules.is_number, description=u'Radius最大会话时长(秒)', help=u'用户在线达到最大会话时长时会自动断开', **input_style), btforms.Dropdown('radius_auth_auto_unlock', args=booleans.items(), description=u'并发自动解锁', help=u'如果账号被挂死，认证时自动踢下线', **input_style), btforms.Dropdown('radius_coa_send_nasaddr', args=booleans.items(), description=u'强制下线是否发送NAS地址', **input_style), btforms.Dropdown('radius_user_trace', args=booleans.items(), description=u'开启用户消息跟踪', help=u'开启此项会记录用户最近认证消息，可用于跟踪用户故障，参考用户管理-用户账号诊断', **input_style), btforms.Dropdown('radius_reject_message', args=booleans.items(), description=u'认证拒绝包含详情消息', help=u'开启此项会在认证拒绝响应中包含详细原因', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'参数配置管理', action='/admin/param/update?active=radcfg')
else:
    rad_form = btforms.Form(btforms.Dropdown('radius_bypass', args=bool_bypass.items(), description=u'Radius认证模式', **input_style), btforms.Textbox('radius_acct_interim_intelval', rules.is_number, description=u'Radius记账间隔(秒)', help=u'radius向bas设备下发的全局记账间隔，bas不支持则不生效', readonly='readonly', **input_style), btforms.Textbox('radius_max_session_timeout', rules.is_number, description=u'Radius最大会话时长(秒)', help=u'用户在线达到最大会话时长时会自动断开', readonly='readonly', **input_style), btforms.Dropdown('radius_auth_auto_unlock', args=booleans.items(), description=u'并发自动解锁', help=u'如果账号被挂死，认证时自动踢下线', **input_style), btforms.Dropdown('radius_user_trace', args=booleans.items(), description=u'开启用户消息跟踪', help=u'开启此项会记录用户最近认证消息，可用于跟踪用户故障，参考用户管理-用户账号诊断', **input_style), title=u'参数配置管理', action='/admin/param/update?active=radcfg')
if not os.environ.get('DEMO_VER'):
    alipay_form = btforms.Form(btforms.Textbox('ALIPAY_PARTNER', description=u'合作伙伴ID', **input_style), btforms.Password('ALIPAY_KEY', description=u'安全密钥', **input_style), btforms.Textbox('ALIPAY_SELLER_EMAIL', description=u'企业支付宝账号', **input_style), btforms.Textbox('ALIPAY_NOTIFY_URL', description=u'支付结果通知地址', **input_style), btforms.Textbox('ALIPAY_RETURN_URL', description=u'支付完成返回地址', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'支付宝参数设置', action='/admin/param/update?active=alipaycfg')
else:
    alipay_form = btforms.Form(btforms.Textbox('ALIPAY_NOTIFY_URL', description=u'支付结果通知地址', readonly='readonly', **input_style), btforms.Textbox('ALIPAY_RETURN_URL', description=u'支付完成返回地址', readonly='readonly', **input_style), title=u'支付宝参数设置', action='/admin/param/update?active=alipaycfg')
if os.environ.get('DEMO_VER'):

    def mps_form():
        return btforms.Form(btforms.Textbox('mps_apiurl', description=u'微信公众号接口地址', readonly='readonly', **input_style), btforms.Textbox('mps_appid', description=u'微信公众号应用ID', readonly='readonly', **input_style), btforms.Dropdown('mps_encrypt_mode', args=en_modes.items(), description=u'微信公众号消息加解密模式', **input_style), btforms.Textarea('mps_welcome_text', description=u'公众号欢迎信息', rows=5, readonly='readonly', **input_style), title=u'微信公众号配置管理(演示配置)', action='/admin/param/update?active=mpscfg')


else:

    def mps_form():
        return btforms.Form(btforms.Textbox('mps_apiurl', description=u'微信公众号接口地址', **input_style), btforms.Password('mps_token', description=u'微信公众号令牌(Token)', **input_style), btforms.Textbox('mps_appid', description=u'微信公众号应用ID', **input_style), btforms.Password('mps_apisecret', description=u'微信公众号应用密钥', **input_style), btforms.Password('mps_encoding_aes_key', description=u'微信公众号消息加解密密钥', **input_style), btforms.Dropdown('mps_encrypt_mode', args=en_modes.items(), description=u'微信公众号消息加解密模式', **input_style), btforms.Textbox('mps_dnsv_upload', description=u'域名验证文件', type='button', **input_style), btforms.Textarea('mps_welcome_text', description=u'公众号欢迎信息', rows=5, hr=True, **input_style), btforms.Dropdown('mps_wxpay_enable', args=booleans.items(), description=u'启用微信支付', **input_style), btforms.Textbox('mps_wxpay_mch_id', description=u'微信支付商户号', **input_style), btforms.Password('mps_wxpay_key', description=u'微信支付Key', **input_style), btforms.Textbox('mps_wxpay_ip', description=u'微信支付商户网站IP', **input_style), btforms.Textbox('mps_wxpay_notify_url', description=u'微信支付结果通知URL', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'微信公众号配置管理', action='/admin/param/update?active=mpscfg')


def adconfig_form(nodes = [], **kwargs):
    form = btforms.Form(title=u'高级参数设置', action='/admin/param/update?active=adconfig')
    items = form.inputs = []
    items.append(btforms.Dropdown('system_api_enable', args=booleans.items(), description=u'启用API接口', **input_style))
    items.append(btforms.Textbox('system_ticket_expire_days', description=u'上网日志保留天数', **input_style))
    items.append(btforms.Textbox('expire_notify_days', rules.is_number, description=u'到期提醒提前天数', **input_style))
    items.append(btforms.Textbox('expire_ipaddr_pool', description=u'到期用户下发地址池', help=u'到期，余额不足用户下发,不使用可填写none', **input_style))
    items.append(btforms.Dropdown('renew_time_type', args=renew_time_types.items(), description=u'续费模式', **input_style))
    items.append(btforms.Dropdown('default_user_node_id', args=nodes, description=u'默认用户区域', help=u'自助开户使用', **input_style))
    items.append(btforms.Textbox('billtask_last_day', rules.is_number, description=u'用户账单任务截止日期(1-28)', **input_style))
    items.append(btforms.Dropdown('billing_fee_precision', args=fee_precisions.items(), description=u'后付费账单金额精度(元/分)', **input_style))
    items.append(btforms.Dropdown('ssportal_smsvcode_required', args=booleans.items(), description=u'自助注册开户采用短信验证', **input_style))
    items.append(btforms.Dropdown('ssportal_allow_release_bind', args=booleans.items(), description=u'自助服务允许清除Mac绑定', **input_style))
    items.append(btforms.Dropdown('ssportal_allow_online_unlock', args=booleans.items(), description=u'自助服务允许下线操作', **input_style))
    items.append(btforms.Textarea('ssportal_paydone_text', description=u'自助服务支付完成提示信息(支持html)', rows=5, **input_style))
    items.append(btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style))
    return form