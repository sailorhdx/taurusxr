#!/usr/bin/env python
# coding=utf-8
import os
from taurusxradius.taurusxlib import logger
from taurusxradius.taurusxlib import utils
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.modules.mps.base import BaseHandler
from twisted.internet import defer
from taurusxradius.modules import models
from urllib import urlencode
from taurusxradius.common import tools
import base64

@permit.route('/mps/faqs')

class MpsFaqsHandler(BaseHandler):

    def get(self):
        self.render('faqs.html')