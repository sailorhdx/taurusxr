#!/usr/bin/env python
# coding=utf-8
import time
from taurusxradius.taurusxlib import utils
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules.wlanportal.base import BaseHandler
from twisted.internet import defer
import functools

@permit.route('/navigate')

class NavgateHandler(BaseHandler):

    def get(self):
        self.render('navigate.html')