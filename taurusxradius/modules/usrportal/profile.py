#!/usr/bin/env python
# coding=utf-8

from taurusxradius.modules.usrportal.base import BaseHandler
from taurusxradius.taurusxlib.permit import permit

@permit.route('/usrportal/profile')

class UsrPortalProfileHandler(BaseHandler):

    def get(self):
        if not self.current_user:
            self.redirect('/usrportal/login')
            return
        else:
            self.render('profile_index.html')
            return