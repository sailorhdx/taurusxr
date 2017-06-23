#!/usr/bin/env python
# coding=utf-8
from taurusxradius.modules.radius.radius_basic import RadiusBasic
from taurusxradius.taurusxlib.storage import Storage
from taurusxradius.modules import models
from taurusxradius.taurusxlib import utils, dispatch, logger
from taurusxradius.modules.settings import *

class RadiusAcctOnoff(RadiusBasic):

    def __init__(self, dbengine = None, cache = None, aes = None, request = None):
        RadiusBasic.__init__(self, dbengine, cache, aes, request)

    def acctounting(self):
        logger.info('bas accounting onoff success')