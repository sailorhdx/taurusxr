#!/usr/bin/env python
# coding=utf-8
from toughradius.modules.radius.radius_basic import RadiusBasic
from toughradius.toughlib.storage import Storage
from toughradius.modules import models
from toughradius.toughlib import utils, dispatch, logger
from toughradius.modules.settings import *

class RadiusAcctOnoff(RadiusBasic):

    def __init__(self, dbengine = None, cache = None, aes = None, request = None):
        RadiusBasic.__init__(self, dbengine, cache, aes, request)

    def acctounting(self):
        logger.info('bas accounting onoff success')