#!/usr/bin/env python
# coding=utf-8
import datetime
import time
from toughradius.modules.ssportal.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models

@permit.route('/')

class HomeHandler(BaseHandler):

    def get(self):
        self.render('index.html')


@permit.route('/ssportal')

class SSportalHandler(BaseHandler):

    def get(self):
        self.render('index.html')