#!/usr/bin/env python
# coding=utf-8
import time
from toughradius.toughlib import utils
from toughradius.toughlib.permit import permit
from toughradius.modules.wlanportal.base import BaseHandler
from twisted.internet import defer
import functools

@permit.route('/navigate')

class NavgateHandler(BaseHandler):

    def get(self):
        self.render('navigate.html')