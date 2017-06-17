#!/usr/bin/env python
# coding=utf-8
import time
import traceback
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib import utils, apiutils, dispatch, logger
from toughradius.toughlib.permit import permit
from toughradius.modules.api.apibase import ApiHandler
from toughradius.modules.api.apibase import authapi
from toughradius.modules import models

@permit.route('/api/v1/product/query')

class ProductQueryHandler(ApiHandler):

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            product_id = formdata.get('product_id')
            products = self.db.query(models.TrProduct)
            if product_id:
                products = products.filter_by(id=product_id)
            product_datas = []
            for product in products:
                product_data = {c.name:getattr(product, c.name) for c in product.__table__.columns}
                product_datas.append(product_data)

            self.render_success(data=product_datas)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)