#!/usr/bin/env python
# coding=utf-8
from toughradius.modules.mps.base import BaseHandler
from toughradius.modules.dbservice.customer_add import CustomerAdd
from toughradius.modules.dbservice.account_renew import AccountRenew
from toughradius.modules.dbservice.account_charge import AccountCharge
from toughradius.common import tools
from toughradius.modules import models
from toughradius.toughlib.btforms import rules
from toughradius.toughlib import logger
from toughradius.toughlib import utils
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.permit import permit
from toughradius.modules.settings import order_wxpaycaache_key
from urllib import urlencode
import json
import string
import decimal
import datetime
import os

@permit.route('/mps/wxorder/pay/(\\w+)')

class WxpayOrderPayHandler(BaseHandler):

    def get(self, orderid):
        try:
            openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
            if not openid:
                cbk_param = urlencode({'cbk': '/mps/wxorder/pay/%s' % orderid})
                return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
            order_data = self.paycache.get(order_wxpaycaache_key(orderid))
            product = self.db.query(models.TrProduct).filter_by(id=order_data.product_id).first()
            if not product:
                return self.render('error.html', msg=u'资费不存在')
            order_product = {'product_id': order_data.product_id,
             'attach': order_data.order_attach,
             'body': order_data.wxpay_body,
             'out_trade_no': order_data.order_id,
             'total_fee': float(order_data.fee_value)}
            ret_dict = self.wxpay.generate_jsapi(order_product, openid)
            ret_str = u'\n            <html>\n            <head></head>\n            <body>\n            <script type="text/javascript">\n            function callpay()\n            {\n                if (typeof WeixinJSBridge == "undefined"){\n                    if( document.addEventListener ){\n                        document.addEventListener(\'WeixinJSBridgeReady\', jsApiCall, false);\n                    }else if (document.attachEvent){\n                        document.attachEvent(\'WeixinJSBridgeReady\', jsApiCall); \n                        document.attachEvent(\'onWeixinJSBridgeReady\', jsApiCall);\n                    }\n                }else{\n                    jsApiCall();\n                }\n            }\n            //alert("ddd");\n            function jsApiCall(){\n                //alert("in");\n                WeixinJSBridge.invoke(\n                    \'getBrandWCPayRequest\',\n                    %s,\n                    function(res){\n                        //alert(JSON.stringify(res));\n                        if(res.err_msg == "get_brand_wcpay_request:ok" ) {\n                            window.location.href = "/mps/userinfo";\n                        } else if(res.err_msg == "get_brand_wcpay_request:cancel"){\n                            window.location.href = "/mps/products";\n                        }else{\n                            alert("交易失败，请联系客服")\n                            window.location.href = "/mps/products";\n                        }\n                    }\n                );\n            }\n            callpay();\n            </script>\n            </body>\n            </html>\n            ' % json.dumps(ret_dict)
            self.write(ret_str)
        except Exception as err:
            logger.exception(err)
            self.render('error.html', msg=u'交易失败，请联系客服 %s' % repr(err))


@permit.route('/mps/wxpay/notify')

class WxpayCallbackHandler(BaseHandler):
    """微信支付结果通知处理，通过 attach 参数传递支付类型, formdata 缓存订单数据
    neworder : 新开户订单
    reneworder : 续费订单
    rechargeorder : 充值订单
    """
    success = {'return_code': 'SUCCESS',
     'return_msg': 'OK'}
    failure = {'return_code': 'FAIL',
     'return_msg': 'verify error'}

    def send_user_paynotify(self, formdata):
        try:
            openid = formdata.get('openid')
            wmsg = u'尊敬的用户::\n\n您好，您的交易处理成功:\n\n商品: {0}\n账号: {1}\n订单号: {2}\n金额: {3} 元\n\n如有疑问，请联系客服。'
            self.send_notify(openid, wmsg.format(formdata.wxpay_body, formdata.account_number, formdata.order_id, formdata.fee_value))
        except Exception as err:
            logger.exception(err)

    def do_new_order(self, formdata):
        """ 开户订单结果处理
        """
        manager = CustomerAdd(self.db, self.aes)
        if manager.add(formdata):
            self.write(self.wxpay.generate_notify_resp(self.success))
            logger.info('neworder process done', trace='wxpay', order_id=formdata.order_id)
            self.send_user_paynotify(formdata)
        else:
            logger.error(u'收到支付结果通知，但处理订单失败 %s' % manager.last_error, trace='wxpay')

    def do_renew_order(self, formdata):
        """ 续费订单结果处理
        """
        manager = AccountRenew(self.db, self.aes)
        if manager.renew(formdata):
            self.write(self.wxpay.generate_notify_resp(self.success))
            logger.info('reneworder process done', trace='wxpay', order_id=formdata.order_id)
            self.send_user_paynotify(formdata)
        else:
            logger.error(u'收到续费支付结果通知，但处理订单失败 %s' % manager.last_error, trace='wxpay')

    def do_recharge_order(self, formdata):
        """ 充值订单结果处理
        """
        manager = AccountCharge(self.db, self.aes)
        if manager.charge(formdata):
            self.write(self.wxpay.generate_notify_resp(self.success))
            logger.info('reneworder process done', trace='wxpay', order_id=formdata.order_id)
            self.send_user_paynotify(formdata)
        else:
            logger.error(u'收到充值支付结果通知，但处理订单失败 %s' % manager.last_error, trace='wxpay')

    def get(self):
        self.post()

    def post(self):
        try:
            xml_str = self.request.body
            ret, ret_dict = self.wxpay.verify_notify(xml_str)
            if not ret:
                logger.error('order verify_notify failure', trace='wxpay')
                self.write(self.wxpay.generate_notify_resp(self.failure))
                return
            order_id = ret_dict['out_trade_no']
            order_fee = ret_dict['total_fee']
            attach = ret_dict['attach']
            order = self.db.query(models.TrCustomerOrder).get(order_id)
            if order and order.pay_status == 1:
                logger.error(u'order %s already process' % order_id, trace='wxpay')
                self.write(self.wxpay.generate_notify_resp(self.success))
                return
            formdata = self.paycache.get(order_wxpaycaache_key(order_id))
            if not formdata:
                raise ValueError('order %s not exists' % order_id)
            if attach == 'neworder':
                self.do_new_order(formdata)
            elif attach == 'reneworder':
                self.do_renew_order(formdata)
            elif attach == 'rechargeorder':
                self.do_recharge_order(formdata)
            else:
                raise ValueError('unknow order %s' % order_id)
        except Exception as err:
            logger.exception(err, trace='wxpay')
            self.write(self.wxpay.generate_notify_resp(self.failure))