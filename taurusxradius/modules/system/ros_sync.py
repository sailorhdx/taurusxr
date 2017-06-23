#!/usr/bin/env python
# coding=utf-8
import os
import cyclone.web
from taurusxradius.taurusxlib import utils, logger, dispatch
from taurusxradius.modules.base import BaseHandler, authenticated
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules.system import config_forms
from taurusxradius.modules import models
from taurusxradius.modules.settings import *

@permit.suproute('/admin/rossync/addrpool', u'地址池同步', MenuRes, order=11.001, is_menu=False)

class AddrPoolSyncHandler(BaseHandler):

    @authenticated
    def get(self):
        pass


@permit.suproute('/admin/rossync/user', u'pppoe 用户同步', MenuRes, order=11.002, is_menu=False)

class PppoeUserSyncHandler(BaseHandler):

    @authenticated
    def get(self):
        pass


@permit.suproute('/admin/rossync/profile', u'pppoe profile 同步', MenuRes, order=11.003, is_menu=False)

class PppoeProfileSyncHandler(BaseHandler):

    @authenticated
    def get(self):
        pass