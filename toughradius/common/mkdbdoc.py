#!/usr/bin/env python
# coding=utf-8

from toughradius.modules import models

def print_header():
    print '%s  %s  %s  %s' % ('=' * 23,
     '=================',
     '================',
     '=' * 26)
    print '%s  %s  %s  %s' % ('属性'.ljust(26, ' '),
     '类型（长度）'.ljust(25, ' '),
     '可否为空'.ljust(22, ' '),
     '描述'.ljust(30, ' '))
    print '%s  %s  %s  %s' % ('=' * 23,
     '=================',
     '================',
     '=' * 26)


def print_end():
    print '%s  %s  %s  %s' % ('=' * 23,
     '=================',
     '================',
     '=' * 26)


def print_model(tmdl):
    print tmdl.__tablename__
    print '-' * 30
    print '\n::\n'
    if tmdl.__doc__:
        print '    %s' % tmdl.__doc__.strip()
        print
    pk = ','.join((c.name for c in tmdl.__table__.primary_key.columns))
    print_header()
    for c in tmdl.__table__.columns:
        _name = str(c.name).ljust(23, ' ')
        _type = str(c.type).ljust(17, ' ')
        _null = str(c.nullable).ljust(16, ' ')
        _doc = str((c.doc or '').encode('utf-8')).ljust(26, ' ')
        print '%s  %s  %s  %s' % (_name,
         _type,
         _null,
         _doc)

    print_end()


mdls = [models.TrNode,
 models.TrArea,
 models.TrOperator,
 models.TrOperatorNodes,
 models.TrOperatorProducts,
 models.TrOperatorRule,
 models.TrParam,
 models.TrBas,
 models.TrBasNode,
 models.TrRoster,
 models.TrCustomer,
 models.TrCustomerOrder,
 models.TrAccount,
 models.TrAccountAttr,
 models.TrOnline,
 models.TrTicket,
 models.TrProduct,
 models.TrProductAttr,
 models.TrAcceptLog,
 models.TrOperateLog,
 models.TrAccountRule,
 models.TrCharges,
 models.TrProductCharges,
 models.TrChargeLog,
 models.TrCustomerNote,
 models.TrContentTemplate,
 models.TrPrintTemplate,
 models.TrPrintTemplateTypes,
 models.TrIssues,
 models.TrIssuesAppend,
 models.TrIssuesFlow,
 models.TrBuilder,
 models.TrAreaBuilder,
 models.TrAgency,
 models.TrAgencyShare,
 models.TrAgencyOrder,
 models.TrValCard]

def make_doc():
    print '数据字典'
    print '====================='
    for mdl in mdls:
        print_model(mdl)
        print


if __name__ == '__main__':
    print '数据字典'
    print '====================='
    for mdl in mdls:
        print_model(mdl)
        print