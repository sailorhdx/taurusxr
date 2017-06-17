#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib.dbutils import make_db
from toughradius.modules import models
from toughradius.toughlib import logger

class TaseBasic:

    def __init__(self, taskd, **kwargs):
        self.config = taskd.config
        self.db = taskd.db
        self.cache = taskd.cache
        self.time_count = 1

    def logtimes(self):
        pass

    def first_delay(self):
        return 120.0

    def process(self, *args, **kwargs):
        pass

    def format_time(self, times):
        if times <= 60:
            return u'%s秒' % times
        d = times / 86400
        h = times % 86400 / 3600
        m = times % 86400 % 3600 / 60
        s = times % 86400 % 3600 % 60
        if int(d) > 0:
            return u'%s天%s小时%s分钟%s秒' % (int(d),
             int(h),
             int(m),
             int(s))
        if int(d) == 0 and int(h) > 0:
            return u'%s小时%s分钟%s秒' % (int(h), int(m), int(s))
        if int(d) == 0 and int(h) == 0 and int(m) > 0:
            return u'%s分钟%s秒' % (int(m), int(s))

    def get_param_value(self, name, defval = None):
        with make_db(self.db) as conn:
            val = self.db.query(models.TrParam.param_value).filter_by(param_name=name).scalar()
            return val or defval