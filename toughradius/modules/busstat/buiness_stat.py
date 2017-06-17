#!/usr/bin/env python
# coding=utf-8
import decimal
import datetime
from sqlalchemy import func
from tablib import Dataset
from toughradius.modules import models
from toughradius.modules.customer import customer_forms
from toughradius.modules.base import authenticated
from toughradius.modules.base import BaseHandler
from toughradius.toughlib.permit import permit
from toughradius.toughlib import utils
from toughradius.modules.settings import *

@permit.suproute('/admin/stat/buiness', u'运营统计分析', MenuStat, order=6.0, is_menu=True)

class BuinessStatHandler(BaseHandler):

    @authenticated
    def get(self):
        self.render('business_stat.html')