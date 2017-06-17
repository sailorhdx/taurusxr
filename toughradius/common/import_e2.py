#!/usr/bin/env python
# coding=utf-8
import sys
import os
import time
import datetime
import traceback
sys.path.insert(0, os.path.split(__file__)[0])
sys.path.insert(0, os.path.abspath(os.path.pardir))
from toughradius.toughlib import utils
from toughradius.modules import models
from toughradius.toughlib.dbengine import get_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from toughradius.modules.settings import *
from toughradius.common import tools
from toughradius.common import model211
from toughradius.common import model20
from sqlalchemy.sql import text as _sql
from hashlib import md5

def newid(oid):
    if not oid:
        return oid
    return md5(str(oid)).hexdigest()


def cut_result(results, rate = 32):
    size = len(results) / rate + 1
    rmap = {}
    for idx, val in enumerate(results):
        rmap.setdefault(idx % size, []).append(val)

    return rmap.itervalues()


def import_params(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_param'].select()):
            item = dict(row)
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(_sql('delete from tr_param'))
            db.execute(ometadata.tables['tr_param'].insert().values(rs))
            print '- Append into table tr_param %s rows' % len(rs)


def import_node(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_node'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            item['rule_id'] = newid(item['rule_id'])
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_node'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_node'].insert().values(rs))
            print '- Append into table tr_node %s rows' % len(rs)


def import_area(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_area'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            item['node_id'] = newid(item['node_id'])
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_area'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_area'].insert().values(rs))
            print '- Append into table tr_area %s rows' % len(rs)


def import_opr(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_operator'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_operator'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_operator'].insert().values(rs))
            print '- Append into table tr_operator %s rows' % len(rs)


def import_opr_nodes(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_operator_nodes'].select()):
            item = dict(row)
            item['node_id'] = newid(item['node_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_operator_nodes'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_operator_nodes'].insert().values(rs))
            print '- Append into table tr_operator_nodes %s rows' % len(rs)


def import_opr_products(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_operator_products'].select()):
            item = dict(row)
            item['product_id'] = newid(item['product_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_operator_products'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_operator_products'].insert().values(rs))
            print '- Append into table tr_operator_products %s rows' % len(rs)


def import_opr_rule(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_operator_rule'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_operator_rule'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_operator_rule'].insert().values(rs))
            print '- Append into table tr_operator_rule %s rows' % len(rs)


def import_bas(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_bas'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_bas'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_bas'].insert().values(rs))
            print '- Append into table tr_bas %s rows' % len(rs)


def import_bas_node(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_bas_node'].select()):
            item = dict(row)
            item['bas_id'] = newid(item['bas_id'])
            item['node_id'] = newid(item['node_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_bas_node'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_bas_node'].insert().values(rs))
            print '- Append into table tr_bas_node %s rows' % len(rs)


def import_customer(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_customer'].select()):
            item = dict(row)
            item['customer_id'] = newid(item['customer_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            item['agency_id'] = ''
            item['node_id'] = newid(item['node_id'])
            item['area_id'] = newid(item['area_id'])
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_customer'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_customer'].insert().values(rs))
            print '- Append into table tr_customer %s rows' % len(rs)


def import_customer_order(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_customer_order'].select()):
            item = dict(row)
            item['customer_id'] = newid(item['customer_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            item['product_id'] = newid(item['product_id'])
            item['accept_id'] = newid(item['accept_id'])
            item['stat_year'] = item['create_time'][0:4]
            item['stat_month'] = item['create_time'][0:7]
            item['stat_day'] = item['create_time'][0:10]
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_customer_order'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_customer_order'].insert().values(rs))
            print '- Append into table tr_customer_order %s rows' % len(rs)


def import_account(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_account'].select()):
            item = dict(row)
            item['customer_id'] = newid(item['customer_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            item['product_id'] = newid(item['product_id'])
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_account'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_account'].insert().values(rs))
            print '- Append into table tr_account %s rows' % len(rs)


def import_account_attr(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_account_attr'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_account_attr'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_account_attr'].insert().values(rs))
            print '- Append into table tr_account_attr %s rows' % len(rs)


def import_account_rule(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_account_rule'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_account_rule'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_account_rule'].insert().values(rs))
            print '- Append into table tr_account_rule %s rows' % len(rs)


def import_product(imetadata, ometadata, rate = 32, imetadata20 = None):
    """ \xe7\x89\x88\xe6\x9c\xac20\xe6\xb2\xa1\xe6\x9c\x89 free_auth \xe5\xb1\x9e\xe6\x80\xa7\xef\xbc\x8c\xe9\x9c\x80\xe8\xa6\x81\xe5\x81\x9a\xe9\xa2\x9d\xe5\xa4\x96\xe5\xa4\x84\xe7\x90\x86
    """
    try:
        results = []
        with imetadata.bind.begin() as db:
            for row in db.execute(imetadata.tables['tr_product'].select()):
                item = dict(row)
                item['id'] = newid(item['id'])
                item['sync_ver'] = tools.gen_sync_ver()
                results.append(item)

        with ometadata.bind.begin() as db:
            db.execute(_sql('delete from tr_product'))
        for rs in cut_result(results, rate=rate):
            with ometadata.bind.begin() as db:
                db.execute(ometadata.tables['tr_product'].insert().values(rs))
                db.execute(_sql('delete from tr_product where product_policy=6'))
                print '- Append into table tr_product %s rows' % len(rs)

    except:
        print 'import v211 error , try import v20'
        results = []
        with imetadata20.bind.begin() as db:
            for row in db.execute(imetadata20.tables['tr_product'].select()):
                item = dict(row)
                item['id'] = newid(item['id'])
                item['sync_ver'] = tools.gen_sync_ver()
                item['free_auth'] = 0
                item['free_auth_uprate'] = 0
                item['free_auth_downrate'] = 0
                results.append(item)

        with ometadata.bind.begin() as db:
            db.execute(_sql('delete from tr_product'))
        for rs in cut_result(results, rate=rate):
            with ometadata.bind.begin() as db:
                db.execute(ometadata.tables['tr_product'].insert().values(rs))
                db.execute(_sql('delete from tr_product where product_policy=6'))
                print '- Append into table tr_product %s rows' % len(rs)


def import_product_attr(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_product_attr'].select()):
            item = dict(row)
            item['product_id'] = newid(item['product_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_product_attr'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_product_attr'].insert().values(rs))
            print '- Append into table tr_product_attr %s rows' % len(rs)


def import_accept_log(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_accept_log'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            item['stat_year'] = item['accept_time'][0:4]
            item['stat_month'] = item['accept_time'][0:7]
            item['stat_day'] = item['accept_time'][0:10]
            results.append(item)

        with ometadata.bind.begin() as db:
            db.execute(_sql('delete from tr_accept_log'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_accept_log'].insert().values(rs))
            print '- Append into table tr_accept_log %s rows' % len(rs)


def import_operate_log(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_operate_log'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(_sql('delete from tr_operate_log'))
            db.execute(ometadata.tables['tr_operate_log'].insert().values(rs))
            print '- Append into table tr_operate_log %s rows' % len(rs)


def import_charges(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_charges'].select()):
            item = dict(row)
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(_sql('delete from tr_charges'))
            db.execute(ometadata.tables['tr_charges'].insert().values(rs))
            print '- Append into table tr_charges %s rows' % len(rs)


def import_product_charges(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_product_charges'].select()):
            item = dict(row)
            item['product_id'] = newid(item['product_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(_sql('delete from tr_product_charges'))
            db.execute(ometadata.tables['tr_product_charges'].insert().values(rs))
            print '- Append into table tr_product_charges %s rows' % len(rs)


def import_charge_log(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_charge_log'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_charge_log'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_charge_log'].insert().values(rs))
            print '- Append into table tr_charge_log %s rows' % len(rs)


def import_customer_note(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_customer_note'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['note_id'] = newid(item['note_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_customer_note'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_customer_note'].insert().values(rs))
            print '- Append into table tr_customer_note %s rows' % len(rs)


def import_content_tempalte(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_content_tempalte'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_content_tempalte'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_content_tempalte'].insert().values(rs))
            print '- Append into table tr_content_tempalte %s rows' % len(rs)


def import_print_tempalte(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_print_tempalte'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_print_tempalte'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_print_tempalte'].insert().values(rs))
            print '- Append into table tr_print_tempalte %s rows' % len(rs)


def import_print_tempalte_types(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_print_tempalte_types'].select()):
            item = dict(row)
            item['tpl_id'] = newid(item['tpl_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_print_tempalte_types'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_print_tempalte_types'].insert().values(rs))
            print '- Append into table tr_print_tempalte_types %s rows' % len(rs)


def import_issues(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_issues'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_issues'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_issues'].insert().values(rs))
            print '- Append into table tr_issues %s rows' % len(rs)


def import_issues_append(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_issues_append'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['issues_id'] = newid(item['issues_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_issues_append'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_issues_append'].insert().values(rs))
            print '- Append into table tr_issues_append %s rows' % len(rs)


def import_issues_flow(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_issues_flow'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['issues_id'] = newid(item['issues_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_issues_flow'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_issues_flow'].insert().values(rs))
            print '- Append into table tr_issues_flow %s rows' % len(rs)


def import_builder(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_builder'].select()):
            item = dict(row)
            item['id'] = newid(item['id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_builder'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_builder'].insert().values(rs))
            print '- Append into table tr_builder %s rows' % len(rs)


def import_area_builder(imetadata, ometadata, rate = 32, **kwargs):
    results = []
    with imetadata.bind.begin() as db:
        for row in db.execute(imetadata.tables['tr_area_builder'].select()):
            item = dict(row)
            item['area_id'] = newid(item['area_id'])
            item['builder_id'] = newid(item['builder_id'])
            item['sync_ver'] = tools.gen_sync_ver()
            results.append(item)

    with ometadata.bind.begin() as db:
        db.execute(_sql('delete from tr_area_builder'))
    for rs in cut_result(results, rate=rate):
        with ometadata.bind.begin() as db:
            db.execute(ometadata.tables['tr_area_builder'].insert().values(rs))
            print '- Append into table tr_area_builder %s rows' % len(rs)


funcs = [import_params,
 import_node,
 import_area,
 import_opr,
 import_opr_nodes,
 import_opr_products,
 import_opr_rule,
 import_bas,
 import_bas_node,
 import_customer,
 import_customer_order,
 import_account,
 import_account_attr,
 import_account_rule,
 import_product,
 import_product_attr,
 import_accept_log,
 import_operate_log,
 import_charges,
 import_product_charges,
 import_charge_log,
 import_customer_note,
 import_content_tempalte,
 import_print_tempalte,
 import_print_tempalte_types,
 import_issues,
 import_issues_append,
 import_issues_flow,
 import_builder,
 import_area_builder]

def import_data(idb, odb, rate):
    imetadata20 = model20.get_metadata(idb)
    imetadata211 = model211.get_metadata(idb)
    ometadata = models.get_metadata(odb)
    for _func in funcs:
        try:
            print
            print '*' * 120
            print '* [TaurusXR] Execute Import Function :::: %s' % _func.__name__
            print '*' * 120
            _func(imetadata211, ometadata, rate=rate, imetadata20=imetadata20)
            print '-' * 120
            print
        except Exception as e:
            print '* [TaurusXR] Execute Import Funtion %s Error %s' % (_func, traceback.format_exc()[0:2048])