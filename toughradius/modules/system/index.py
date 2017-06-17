#!/usr/bin/env python
# coding=utf-8
import cyclone.auth
import cyclone.escape
import cyclone.web
import datetime
import time
from beaker.cache import cache_managers
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.toughlib.permit import permit
from toughradius.modules import models
from toughradius.modules.settings import *

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