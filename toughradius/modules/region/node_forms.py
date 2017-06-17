#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}
boolean = {0: u'否',
 1: u'是'}
node_types = {'other': u'未定义',
 'pppoe': u'PPPoE',
 'hotspot': u'HotSpot'}

def node_add_form(rule_ids = [], bas_ids = []):
    return btforms.Form(btforms.Textbox('node_name', rules.len_of(2, 32), description=u'区域名称', required='required', **input_style), btforms.Dropdown('node_type', description=u'区域接入类型', args=node_types.items(), required='required', help=u'仅提供设备同步使用', **input_style), btforms.Dropdown('rule_id', description=u'账号生成规则', args=rule_ids, required='required', **input_style), btforms.Dropdown('bas_id', description=u'绑定接入设备', args=bas_ids, multiple='multiple', size=6, **input_style), btforms.Textarea('node_desc', rules.len_of(2, 128), description=u'区域描述', rows=3, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'创建区域', htopic='node', action='/admin/node/add')


def node_update_form(rule_ids = [], bas_ids = []):
    return btforms.Form(btforms.Hidden('id', description=u'区域ID'), btforms.Textbox('node_name', rules.len_of(2, 32), description=u'区域名称', **input_style), btforms.Dropdown('node_type', description=u'区域接入类型', args=node_types.items(), required='required', help=u'仅提供设备同步使用', **input_style), btforms.Dropdown('rule_id', description=u'账号生成规则', args=rule_ids, required='required', **input_style), btforms.Dropdown('bas_id', description=u'绑定接入设备', args=bas_ids, multiple='multiple', size=6, **input_style), btforms.Textarea('node_desc', rules.len_of(2, 128), description=u'区域描述', rows=3, required='required', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'修改区域', htopic='node', action='/admin/node/update')