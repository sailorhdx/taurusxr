#!/usr/bin/env python
# coding=utf-8
from twisted.internet import defer
from toughradius.modules import models
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.dbutils import make_db
from toughradius.toughlib import logger
from toughradius.toughlib import utils

class WechatEventDispatch:

    @defer.inlineCallbacks
    def wxrouter_customer_service(self, msg, gdata = None, wechat = None, isp_code = None, **kwargs):
        """ 帮助信息 """
        yield
        articles = []
        mp_domain_addr = gdata.get_param_value('mp_domain_addr')
        if not mp_domain_addr:
            logger.error(u'未设置微信公众号域名')
            defer.returnValue(wechat.response_news(articles))
        article1 = Storage()
        article1.title = u'账号管理'
        article1.description = ''
        article1.url = '%s/mps/userbind' % mp_domain_addr
        article1.picurl = ''
        articles.append(article1)
        article2 = Storage()
        article2.title = u'交易记录'
        article2.description = ''
        article2.url = '%s/mps/userorder' % mp_domain_addr
        article2.picurl = ''
        articles.append(article2)
        article3 = Storage()
        article3.title = u'密码修改'
        article3.description = ''
        article3.url = '%s/mps/useruppw' % mp_domain_addr
        article3.picurl = ''
        articles.append(article3)
        article4 = Storage()
        article4.title = u'资费套餐'
        article4.description = ''
        article4.url = '%s/mps/products' % mp_domain_addr
        article4.picurl = ''
        articles.append(article4)
        defer.returnValue(wechat.response_news(articles))


router = WechatEventDispatch()