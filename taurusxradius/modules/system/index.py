#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import datetime
import time
from beaker.cache import cache_managers
from taurusxradius.modules.base import BaseHandler, authenticated
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules import models
from taurusxradius.modules.settings import *

@permit.route('/admin')

class HomeHandler(BaseHandler):

    @authenticated
    def get(self):
        self.redirect('/admin/dashboard')


@permit.route('/')

class HomeHandler(BaseHandler):

    @authenticated
    def get(self):
        self.redirect('/admin/dashboard')


@permit.route('/about')

class HomeHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('about.html')