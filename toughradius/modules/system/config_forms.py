#!/usr/bin/env python
#coding:utf-8
import os
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}
lbutton_style = {'class': 'btn btn-sm btn-link'}
boolean = {0: u'否',
 1: u'是'}
booleans = {'0': u'否',
 '1': u'是'}
timezones = {'CST-8': u'Asia/Shanghai'}
loglevels = {'INFO': u'一般',
 'DEBUG': u'调试',
 'WARNING': u'警告',
 'ERROR': u'错误'}
if not os.environ.get('DEMO_VER') and os.environ.get('LICENSE_TYPE') != 'community':
    system_form = btforms.Form(btforms.Dropdown('debug', args=boolean.items(), description=u'开启DEBUG', help=u'开启此项，可以获取更多的系统日志纪录', **input_style), btforms.Dropdown('tz', args=timezones.items(), description=u'时区', **input_style), btforms.Textbox('license_upload', description=u'授权文件', type='button', **input_style), btforms.Button('reqlicense', type='button', html=u'<b>申请软件授权</b>', onclick='go_request_license()', **lbutton_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'系统配置管理', action='/admin/config/system/update')
else:
    system_form = btforms.Form(btforms.Dropdown('debug', args=boolean.items(), description=u'开启DEBUG', help=u'开启此项，可以获取更多的系统日志纪录', **input_style), btforms.Dropdown('tz', args=timezones.items(), description=u'时区', **input_style), title=u'系统配置管理', action='/admin/config/system/update')
dbtypes = {'mysql': u'mysql',
 'sqlite': u'sqlite'}
if not os.environ.get('DEMO_VER'):
    database_form = btforms.Form(btforms.Dropdown('echo', args=boolean.items(), description=u'开启数据库DEBUG', help=u'开启此项，可以在控制台打印SQL语句', **input_style), btforms.Textbox('dbtype', description=u'数据库类型', readonly='readonly', **input_style), btforms.Textbox('pool_size', description=u'连接池大小', **input_style), btforms.Textbox('pool_recycle', description=u'连接池回收间隔（秒）', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'数据库配置管理', action='/admin/config/database/update')
else:
    database_form = btforms.Form(btforms.Dropdown('echo', args=boolean.items(), description=u'开启数据库DEBUG', help=u'开启此项，可以在控制台打印SQL语句', **input_style), btforms.Textbox('dbtype', description=u'数据库类型', readonly='readonly', **input_style), btforms.Textbox('pool_size', description=u'连接池大小', readonly='readonly', **input_style), btforms.Textbox('pool_recycle', description=u'连接池回收间隔（秒）', readonly='readonly', **input_style), title=u'数据库配置管理', action='/admin/config/database/update')
if not os.environ.get('DEMO_VER'):
    syslog_form = btforms.Form(btforms.Dropdown('enable', args=boolean.items(), description=u'开启syslog', **input_style), btforms.Textbox('server', description=u'syslog 服务器', **input_style), btforms.Textbox('port', description=u'syslog 服务端口(UDP)', **input_style), btforms.Dropdown('level', args=loglevels.items(), description=u'日志级别', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'syslog 配置管理', action='/admin/config/syslog/update')
else:
    syslog_form = btforms.Form(btforms.Dropdown('enable', args=boolean.items(), description=u'开启syslog', **input_style), btforms.Textbox('server', description=u'syslog 服务器', **input_style), btforms.Textbox('port', description=u'syslog 服务端口(UDP)', **input_style), btforms.Dropdown('level', args=loglevels.items(), description=u'日志级别', **input_style), title=u'syslog 配置管理', action='/admin/config/syslog/update')
if not os.environ.get('DEMO_VER'):
    hacfg_form = btforms.Form(btforms.Dropdown('enable', args=boolean.items(), description=u'启用双机热备', help=u'启用后支持双机互为主备，同步数据', **input_style), btforms.Textbox('interval', description=u'同步数据检测间隔', help=u'同步数据间隔的时间，最低支持到1秒', **input_style), btforms.Textbox('ping_interval', description=u'同步链路检测间隔', help=u'链路检测间隔，默认60秒', **input_style), btforms.Textbox('master', description=u'主机地址', help=u'主机地址,格式:tcp://IP地址:端口', **input_style), btforms.Textbox('slave', description=u'备机地址', help=u'备机地址,格式:tcp://IP地址:端口', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'高可用配置管理', action='/admin/config/hacfg/update')
else:
    hacfg_form = btforms.Form(btforms.Dropdown('enable', args=boolean.items(), description=u'启用双机热备', help=u'启用后支持双机互为主备，同步数据', **input_style), btforms.Textbox('interval', description=u'同步数据检测间隔', help=u'同步数据间隔的时间，最低支持到1秒', **input_style), btforms.Textbox('ping_interval', description=u'同步链路检测间隔', help=u'链路检测间隔，默认60秒', **input_style), btforms.Textbox('master', description=u'主机地址', help=u'主机地址,格式:tcp://IP地址:端口', **input_style), btforms.Textbox('slave', description=u'备机地址', help=u'备机地址,格式:tcp://IP地址:端口', **input_style), title=u'高可用配置管理', action='/admin/config/hacfg/update')