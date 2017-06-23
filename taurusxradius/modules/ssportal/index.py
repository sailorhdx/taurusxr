#!/usr/bin/env python
# coding=utf-8
import datetime
import time
from taurusxradius.modules.ssportal.base import BaseHandler, authenticated
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules import models

@permit.route('/')

class HomeHandler(BaseHandler):

    def get(self):
        self.render('index.html')


@permit.route('/ssportal')

class SSportalHandler(BaseHandler):

    def get(self):
        self.render('index.html')