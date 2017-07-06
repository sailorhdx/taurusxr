#!/usr/bin/env python
# coding=utf-8
import datetime
import time

from taurusxradius.modules.customer import customer_forms
from taurusxradius.modules.dbservice.customer_add import CustomerAdd
from taurusxradius.modules.usrportal.base import BaseHandler
from taurusxradius.modules.usrportal import login_form
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils, logger
from taurusxradius.modules import models

@permit.route('/usrportal/profile')

class UsrPortalProfileHandler(BaseHandler):

    def get(self):
        if not self.current_user:
            self.redirect('/usrportal/login')
            return
        else:
            self.render('profile_index.html')
            return