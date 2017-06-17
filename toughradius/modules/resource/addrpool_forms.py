#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.toughlib import btforms
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm bg-navy'}
boolean = {0: u'否',
 1: u'是'}

def pool_add_form():
    return btforms.Form(btforms.Textbox('pool_name', rules.is_alphanum2(1, 64), description=u'地址池名称', required='required', **input_style), btforms.Textbox('start_ip', rules.is_ip, description=u'开始地址', required='required', **input_style), btforms.Textbox('end_ip', rules.is_ip, description=u'结束地址', required='required', **input_style), btforms.Textbox('next_pool', rules.is_alphanum2(1, 64), description=u'下一个地址池', **input_style), btforms.Button('submit', type='submit', html=u'<b>提交</b>', **button_style), title=u'创建地址池', htopic='addrpool', action='/admin/addrpool/add')


def pool_update_form(nodes = []):
    return btforms.Form(btforms.Hidden('id', description=u'编号'), btforms.Textbox('pool_name', rules.is_alphanum2(1, 64), description=u'地址池名称', required='required', **input_style), btforms.Textbox('start_ip', rules.is_ip, description=u'开始地址', required='required', **input_style), btforms.Textbox('end_ip', rules.is_ip, description=u'结束地址', required='required', **input_style), btforms.Textbox('next_pool', rules.is_alphanum2(1, 64), description=u'下一个地址池', **input_style), btforms.Button('submit', type='submit', html=u'<b>更新</b>', **button_style), title=u'修改地址池', htopic='addrpool', action='/admin/addrpool/update')