#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
from toughradius.modules.settings import *
button_style = {'class': 'btn btn-sm'}
issues_types = {'0': u'新装',
 '1': u'故障',
 '2': u'投诉',
 '3': u'其他'}
process_status = {'1': u'处理中',
 '2': u'挂起',
 '3': u'取消',
 '4': u'处理完成'}

def issues_add_form(oprs = []):
    return btforms.Form(btforms.Textbox('account_number', rules.len_of(1, 32), description=u'用户账号', readonly='readonly', **input_style), btforms.Dropdown('issues_type', description=u'工单类型', args=issues_types.items(), **input_style), btforms.Textarea('content', rules.len_of(1, 1024), description=u'工单内容', rows=6, required='required', **input_style), btforms.Dropdown('builder_name', description=u'指派施工人员', args=oprs, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b> 提交 </b>', **button_style), action='/admin/issues/add', title=u'创建用户工单')()


def issues_process_form():
    return btforms.Form(btforms.Hidden('issues_id', rules.len_of(1, 32), description=u'工单id', required='required', **input_style), btforms.Textarea('accept_result', rules.len_of(1, 1024), description=u'处理描述', rows=6, required='required', **input_style), btforms.Dropdown('accept_status', description=u'处理结果', args=process_status.items(), required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b> 处理用户工单 </b>', **button_style), action='/admin/issues/process', title=u'处理用户工单')()