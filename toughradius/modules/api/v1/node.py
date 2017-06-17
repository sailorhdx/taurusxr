#!/usr/bin/env python
# coding=utf-8
import time
import traceback
from toughradius.toughlib.btforms import dataform
from toughradius.toughlib.btforms import rules
from toughradius.toughlib import utils, apiutils, dispatch, logger
from toughradius.toughlib.permit import permit
from toughradius.modules.api.apibase import authapi
from toughradius.modules.api.apibase import ApiHandler
from toughradius.modules import models
from toughradius.modules.dbservice.node_service import NodeService

@permit.route('/api/v1/node/query')

class NodeQueryHandler(ApiHandler):
    """ @param: 
        node_id: str
    """

    def get(self):
        self.post()

    @authapi
    def post(self):
        try:
            formdata = self.parse_form_request()
            node_id = formdata.get('node_id')
            nodes = self.db.query(models.TrNode)
            if node_id:
                nodes = nodes.filter_by(id=node_id)
            node_datas = []
            for node in nodes:
                node_data = {c.name:getattr(node, c.name) for c in node.__table__.columns}
                node_datas.append(node_data)

            self.render_success(data=node_datas)
        except Exception as err:
            logger.exception(err, trace='api')
            return self.render_unknow(err)