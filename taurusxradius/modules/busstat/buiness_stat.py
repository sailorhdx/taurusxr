#!/usr/bin/env python
# coding=utf-8
import decimal
import datetime
from sqlalchemy import func
from tablib import Dataset
from taurusxradius.modules import models
from taurusxradius.modules.customer import customer_forms
from taurusxradius.modules.base import authenticated
from taurusxradius.modules.base import BaseHandler
from taurusxradius.taurusxlib.permit import permit
from taurusxradius.taurusxlib import utils
from taurusxradius.modules.settings import *

@permit.suproute('/admin/stat/buiness', u'运营统计分析', MenuStat, order=6.0, is_menu=True)

class BuinessStatHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('business_stat.html')