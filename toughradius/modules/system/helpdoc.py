#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
import toughradius

@permit.route('/admin/help')

class HelpdocHandler(BaseHandler):

    @authenticated
    def get(self):
        topic = self.get_argument('topic', '')
        mdname = os.path.basename(topic)
        if not mdname:
            mdname = 'default'
        mdpath = os.path.join(os.path.dirname(toughradius.__file__), 'document/{0}.md'.format(mdname))
        print mdpath
        if os.path.exists(mdpath):
            with open(mdpath, 'rb') as fs:
                self.write(fs.read())
        else:
            self.write(u'没有相关的帮助内容')