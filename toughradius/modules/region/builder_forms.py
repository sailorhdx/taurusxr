#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}

def builder_add_form(areas = []):
    return btforms.Form(btforms.Textbox('builder_name', rules.len_of(2, 128), description=u'服务人员姓名', required='required', **input_style), btforms.Textbox('builder_phone', rules.len_of(2, 128), description=u'服务人员电话', required='required', **input_style), btforms.Dropdown('areas', description=u'关联社区', args=areas, multiple='multiple', size=5, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'创建服务人员', htopic='builder', action='/admin/builder/add')


def builder_update_form(areas = []):
    return btforms.Form(btforms.Hidden('id', description=u'ID'), btforms.Textbox('builder_name', rules.len_of(2, 128), description=u'服务人员姓名', required='required', **input_style), btforms.Textbox('builder_phone', rules.len_of(2, 128), description=u'服务人员电话', required='required', **input_style), btforms.Dropdown('areas', description=u'关联社区', args=areas, multiple='multiple', size=5, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'修改服务人员', htopic='builder', action='/admin/builder/update')