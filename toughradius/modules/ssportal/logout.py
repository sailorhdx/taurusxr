#!/usr/bin/env python
# coding=utf-8
from toughradius.modules.ssportal.base import BaseHandler
from toughradius.toughlib.permit import permit

@permit.route('/ssportal/logout')

class LogoutHandler(BaseHandler):

    def get(self):
        if not self.current_user:
            self.redirect('/ssportal/login')
            return
        self.clear_session()
        self.redirect('/ssportal/login', permanent=False)