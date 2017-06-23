#!/usr/bin/env python
# coding=utf-8
from taurusxradius.taurusxlib import utils, dispatch, db_cache
from taurusxradius.taurusxlib import logger
from taurusxradius.modules import models
from taurusxradius.modules.events.event_basic import BasicEvent
from taurusxradius.modules.settings import OpenNotify, account_cache_key
from taurusxradius.modules.events.settings import EVENT_SENDSMS, EVENT_SENDMAIL
from taurusxradius.modules.events.settings import DBSYNC_STATUS_ADD

class AccountDeleteEvent(BasicEvent):

    def event_account_delete(self, account_number):
        logger.info('account delete event:{}'.format(account_number), trace='event')
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAcceptLog.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAccountAttr.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrBilling.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrOnline.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrAccount.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(DBSYNC_STATUS_ADD, models.warp_sdel_obj(models.TrCustomerOrder.__tablename__, dict(account_number=account_number)), async=True)
        dispatch.pub(db_cache.CACHE_DELETE_EVENT, account_cache_key(account_number), async=True)


def __call__(dbengine = None, mcache = None, aes = None, **kwargs):
    return AccountDeleteEvent(dbengine=dbengine, mcache=mcache, aes=aes, **kwargs)