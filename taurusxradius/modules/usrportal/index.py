#!/usr/bin/env python
# coding=utf-8
import datetime
import time
from taurusxradius.modules.usrportal.base import BaseHandler, authenticated
from taurusxradius.taurusxlib import logger
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules import models

@permit.route('/')

class HomeHandler(BaseHandler):

    def get(self):
        self.redirect('/usrportal')
        return

@permit.route('/usrportal')

class UsrPortalHandler(BaseHandler):

    def get(self):
        self.render('usrportal_index.html')