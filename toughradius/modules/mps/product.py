#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import logger
from toughradius.toughlib import utils
from toughradius.toughlib.permit import permit
from toughradius.modules.mps.base import BaseHandler
from twisted.internet import defer
from toughradius.modules import models
from urllib import urlencode
import base64
import os

@permit.route('/mps/products')

class MpsProductHandler(BaseHandler):

    def get(self):
        openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
        if not openid:
            cbk_param = urlencode({'cbk': '/mps/products'})
            return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
        products = self.db.query(models.TrProduct).filter_by(product_status=0, ispub=1)
        self.render('product_list.html', openid=openid, products=products)


@permit.route('/mps/product/(\\w+)')

class MpsProductHandler(BaseHandler):

    def get(self, pid):
        openid = self.session.get('mps_openid', os.environ.get('DEV_OPEN_ID'))
        if not openid:
            cbk_param = urlencode({'cbk': '/mps/product/%s' % pid})
            return self.redirect('/mps/oauth?%s' % cbk_param, permanent=False)
        product = self.db.query(models.TrProduct).filter_by(id=pid).first()
        if not product:
            return self.render('error.html', msg=u'资费不存在')
        self.render('product.html', openid=openid, product=product)