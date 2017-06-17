#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
from toughradius.modules.settings import *
button_style = {'class': 'btn btn-sm'}
tpl_types = {OpenNotify: u'用户开户通知模板',
 NextNotify: u'用户续费通知模板',
 ExpireNotify: u'用户到期通知模板',
 IssuesNotify: u'工单通知模板',
 VcodeNotify: u'验证码通知模板'}
content_tpl_add_form = btforms.Form(btforms.Dropdown('tpl_type', args=tpl_types.items(), description=u'模板类型', required='required', **input_style), btforms.Textbox('tpl_id', rules.not_null, description=u'模板ID', required='required', **input_style), btforms.Textarea('tpl_content', rules.len_of(2, 1024), description=u'模板内容', rows=7, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'创建模板', action='/admin/contenttpl/add')
content_tpl_update_form = btforms.Form(btforms.Hidden('id', description=u'模板ID'), btforms.Dropdown('tpl_type', args=tpl_types.items(), description=u'模板类型', **input_style), btforms.Textbox('tpl_id', rules.not_null, description=u'模板ID', required='required', **input_style), btforms.Textarea('tpl_content', rules.len_of(2, 1024), description=u'模板内容', rows=7, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'修改模板', action='/admin/contenttpl/update')