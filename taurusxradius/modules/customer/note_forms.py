#!/usr/bin/env python
# coding=utf-8
from taurusxradius.taurusxlib import btforms
from taurusxradius.taurusxlib.btforms import rules
from taurusxradius.taurusxlib.btforms.rules import button_style, input_style
button_style = {'class': 'btn btn-sm'}

def note_print_form(tpls = []):
    return btforms.Form(btforms.Dropdown('tpl_id', args=tpls, description=u'票据模板', required='required', **input_style), btforms.Textbox('note_id', rules.len_of(2, 32), description=u'票据凭证号', required='required', readonly='readonly', **input_style), btforms.Textbox('order_id', description=u'缴费订单号', readonly='readonly', **input_style), btforms.Textbox('customer_cname', description=u'客户姓名', required='required', readonly='readonly', **input_style), btforms.Textbox('account_number', description=u'上网账号', readonly='readonly', **input_style), btforms.Textbox('mobile', description=u'手机号码', required='required', readonly='readonly', **input_style), btforms.Textbox('install_address', description=u'客户安装地址', required='required', readonly='readonly', **input_style), btforms.Textbox('pay_type', description=u'付款方式', required='required', readonly='readonly', **input_style), btforms.Textbox('pay_date', description=u'付款日期', required='required', readonly='readonly', **input_style), btforms.Textbox('expire_date', description=u'到期日期', required='required', readonly='readonly', **input_style), btforms.Textbox('order_num', description=u'订购套餐数', required='required', readonly='readonly', **input_style), btforms.Textbox('fee_price', description=u'套餐单价', required='required', readonly='readonly', **input_style), btforms.Textbox('fee_total', description=u'套餐总价', required='required', readonly='readonly', **input_style), btforms.Textarea('remark', description=u'备注内容', rows=4, readonly='readonly', **input_style), btforms.Textbox('operator_name', description=u'收款人', readonly='readonly', **input_style), btforms.Button('doprint', type='button', onclick='doPrint();', html=u'<b>打印预览</b>', **button_style), title=u'用户票据打印', action='/admin/customer/note/print')