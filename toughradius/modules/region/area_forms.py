#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}
boolean = {0: u'否',
 1: u'是'}

def area_add_form(nodes = []):
    return btforms.Form(btforms.Textbox('area_name', rules.len_of(2, 32), description=u'社区名称', required='required', **input_style), btforms.Dropdown('node_id', description=u'所属区域', args=nodes, required='required', **input_style), btforms.Textbox('area_desc', rules.len_of(2, 128), description=u'社区备注', required='required', **input_style), btforms.Textbox('addr_desc', rules.len_of(2, 128), description=u'社区地址描述', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'创建社区', htopic='node', action='/admin/area/add')


def area_update_form(nodes = []):
    return btforms.Form(btforms.Hidden('id', description=u'社区ID'), btforms.Textbox('area_name', rules.len_of(2, 32), description=u'社区名称', **input_style), btforms.Dropdown('node_id', description=u'所属区域', args=nodes, required='required', **input_style), btforms.Textbox('area_desc', rules.len_of(2, 128), description=u'社区备注', required='required', **input_style), btforms.Textbox('addr_desc', rules.len_of(2, 128), description=u'社区地址描述', required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'修改社区', htopic='node', action='/admin/area/update')