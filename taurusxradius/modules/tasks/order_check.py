#!/usr/bin/env python
# coding=utf-8
import sys
import time
import datetime
from taurusxradius.taurusxlib import utils
from taurusxradius.taurusxlib import dispatch, logger
from taurusxradius.modules import models
from taurusxradius.taurusxlib.dbutils import make_db
from taurusxradius.modules.tasks.task_base import TaseBasic
from taurusxradius.modules.events.settings import UNLOCK_ONLINE_EVENT
from taurusxradius.modules.settings import order_paycaache_key
from twisted.internet import reactor
from taurusxradius.modules import taskd

class OrderCheckTask(TaseBasic):
    __name__ = 'order-check'

    def get_next_interval(self):
        return 86400

    def first_delay(self):
        return 5

    def process(self, *args, **kwargs):
        self.logtimes()
        return 300.0


taskd.TaskDaemon.__taskclss__.append(OrderCheckTask)