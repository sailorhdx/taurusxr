#!/usr/bin/env python
# coding=utf-8
import sys
import time
import datetime
from toughradius.toughlib import utils
from toughradius.toughlib import dispatch, logger
from toughradius.modules import models
from toughradius.toughlib.dbutils import make_db
from toughradius.modules.tasks.task_base import TaseBasic
from toughradius.modules.events.settings import UNLOCK_ONLINE_EVENT
from toughradius.modules.settings import order_paycaache_key
from twisted.internet import reactor
from toughradius.modules import taskd

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