#!/usr/bin/env python
# coding=utf-8
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit

@permit.route('/admin/logout')

class LogoutHandler(BaseHandler):

    def get(self):
        if not self.current_user:
            self.redirect('/admin/login')
            return
        self.clear_session()
        self.redirect('/admin/login', permanent=False)