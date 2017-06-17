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
    def wxrouter_menu_products(self, msg, gdata = None, wechat = None, **kwargs):
        """ 套餐资费 """
        yield
        with make_db(gdata.db) as db:
            try:
                mp_domain_addr = self.db.query(models.TrParam.param_value).filter_by(param_name='mp_domain_addr').scalar()
                products = db.query(models.TrProduct).filter_by(product_status=0, ispub=1).limit(7)
                articles = []
                for p in products:
                    article1 = Storage()
                    article1.title = utils.safeunicode(p.product_name)
                    article1.description = ''
                    article1.url = '%s/mps/product/%s' % (mp_domain_addr, p.id)
                    article1.picurl = ''
                    articles.append(article1)

                defer.returnValue(wechat.response_news(articles))
            except Exception as err:
                logger.exception(err, trace='wechat')
                defer.returnValue(wechat.response_text(u'服务器错误,请联系客服 %s' % utils.safeunicode(err)))


router = WechatEventDispatch()