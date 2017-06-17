#!/usr/bin/env python
# coding=utf-8
import os
from toughradius.toughlib import logger
from toughradius.toughlib import utils
from toughradius.toughlib.permit import permit
from toughradius.modules.mps.base import BaseHandler
from twisted.internet import defer
from toughradius.modules import models
from urllib import urlencode
from toughradius.common import tools
import base64

@permit.route('/mps/faqs')

class MpsFaqsHandler(BaseHandler):

    def get(self):
        self.render('faqs.html')