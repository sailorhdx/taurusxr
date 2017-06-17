#!/usr/bin/env python
# coding=utf-8
from sqlalchemy.orm import scoped_session, sessionmaker
from toughradius.modules import models
from toughradius.toughlib.dbutils import make_db
from toughradius.modules.settings import tplid_cache_key
from toughradius.modules.settings import param_cache_key

class BasicEvent:

    def __init__(self, dbengine = None, mcache = None, aes = None, wechat = None, **kwargs):
        self.dbengine = dbengine
        self.mcache = mcache
        self.db = scoped_session(sessionmaker(bind=self.dbengine, autocommit=False, autoflush=False))
        self.aes = aes
        self.wechat = wechat

    def get_param_value(self, name, defval = None):

        def fetch_result():
            table = models.TrParam.__table__
            with self.dbengine.begin() as conn:
                return conn.execute(table.select().with_only_columns([table.c.param_value]).where(table.c.param_name == name)).scalar()

        return self.mcache.aget(param_cache_key(name), fetch_result, expire=300) or defval

    def get_tpl_id(self, tpl_type):

        def fetch_result():
            return self.db.query(models.TrContentTemplate.tpl_id).filter_by(tpl_type=tpl_type).scalar()

        return self.mcache.aget(tplid_cache_key(tpl_type), fetch_result, expire=300)

    def get_customer_info(self, account_number):
        with make_db(self.db) as db:
            return db.query(models.TrCustomer.mobile, models.TrCustomer.email, models.TrCustomer.wechat_oid, models.TrCustomer.realname, models.TrProduct.product_name, models.TrAccount.account_number, models.TrAccount.install_address, models.TrAccount.expire_date, models.TrAccount.password).filter(models.TrCustomer.customer_id == models.TrAccount.customer_id, models.TrAccount.product_id == models.TrProduct.id, models.TrAccount.account_number == account_number).first()

    def get_content_template(self, tpl_type):
        table = models.TrContentTemplate.__table__
        with self.dbengine.begin() as conn:
            return conn.execute(table.select().with_only_columns([table.c.tpl_content]).where(table.c.tpl_type == tpl_type)).scalar()


__call__ = lambda **kwargs: None