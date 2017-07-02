#!/usr/bin/env python
# coding=utf-8
import sys
import os
import time
import datetime
sys.path.insert(0, os.path.split(__file__)[0])
sys.path.insert(0, os.path.abspath(os.path.pardir))
from taurusxradius.taurusxlib import utils
from taurusxradius.modules import models
from taurusxradius.taurusxlib.dbengine import get_engine
from taurusxradius.taurusxlib.db_backup import DBBackup
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text as _sql
from taurusxradius.modules.settings import *
from taurusxradius.common import tools
from hashlib import md5
import random

def init_db(db):
    product = models.TrProduct()
    product.id = '00000000000000000000000000000000'
    product.product_name = '自助注册时长套餐'
    product.ispub = 0
    product.product_policy = 3
    product.product_status = 0
    product.fee_days = 0
    product.fee_months = 0
    product.fee_times = 0
    product.fee_flows = 0
    product.bind_mac = 0
    product.bind_vlan = 0
    product.concur_number = 1
    product.fee_price = 0
    product.fee_period = ''
    product.input_max_limit = utils.mbps2bps(100)
    product.output_max_limit = utils.mbps2bps(100)
    product.free_auth = 0
    product.free_auth_uprate = 0
    product.free_auth_downrate = 0
    _datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    product.create_time = _datetime
    product.update_time = _datetime
    product.sync_ver = tools.gen_sync_ver()
    db.add(product)
    arule = models.TrAccountRule()
    arule.id = 1
    arule.rule_name = u'默认账号生成规则'
    arule.user_prefix = 'user'
    arule.user_suffix_len = 6
    arule.user_sn = 1
    arule.sync_ver = tools.gen_sync_ver()
    db.add(arule)
    node = models.TrNode()
    node.id = 1
    node.rule_id = arule.id
    node.node_name = u'默认区域'
    node.node_desc = u'默认区域'
    node.addr_desc = u'默认区域'
    node.sync_ver = tools.gen_sync_ver()
    db.add(node)
    area = models.TrArea()
    area.id = 1
    area.node_id = node.id
    area.area_name = u'默认小区'
    area.area_desc = u'默认小区'
    area.addr_desc = u'默认小区地址'
    area.sync_ver = tools.gen_sync_ver()
    db.add(area)
    params = [('system_name', u'管理系统名称', u'计费管理控制台'),
     ('system_theme', u'系统风格样式', u'skin-blue'),
     ('login_logo', u'登录页面Logo', u'/static/img/manage_login_logo200X120_radius.png'),
     ('index_logo', u'管理页面Logo', u'/static/img/manage_logo180X38_radius.png'),
     ('login_bgimg', u'登录页面背景图', u'/static/img/manage_login_bg.jpg'),
     ('ssportal_title', u'网上营业厅名称', u'计费网上营业厅'),
     ('ssportal_banner_bg', u'网上营业厅背景图', u'/static/img/ssportal-banner-bg.jpg'),
     ('copy_right', u'版权信息', u'Ⓒ 2014-2017 TaurusX Studio.'),
     ('support_desc', u'技术支持', u''),
     ('system_ticket_expire_days', u'上网日志保留天数', '60'),
     ('is_debug', u'DEBUG模式', u'0'),
     ('expire_notify_days', u'到期提醒提前天数', u'10'),
     ('expire_addrpool', u'到期提醒下发地址池', u'expire'),
     ('expire_session_timeout', u'到期用户下发最大会话时长(秒)', u'0'),
     ('smtp_server', u'SMTP服务器地址', u''),
     ('smtp_port', u'SMTP服务器端口', u'25'),
     ('smtp_user', u'SMTP用户名', u''),
     ('smtp_pwd', u'SMTP密码', u''),
     ('smtp_sender', u'SMTP发送人名称', u'运营中心'),
     ('smtp_from', u'SMTP邮件发送地址', u''),
     ('smtp_tls', u'SMTP邮件启用TLS', u'0'),
     ('mail_notify_enable', u'启动邮件到期提醒', u'0'),
     ('mail_notify_interval', u'邮件到期提醒提前间隔(分钟)', u'1440'),
     ('mail_notify_time', u'邮件到期提醒时间(hh:mm)', u'09:00'),
     ('mail_to', u'测试邮件接收地址', u''),
     ('sms_notify_enable', u'启动短信到期提醒', u'0'),
     ('sms_notify_interval', u'短信到期提醒提前间隔(分钟)', u'1440'),
     ('sms_notify_time', u'短信到期提醒时间(hh:mm)', u'09:00'),
     ('radius_bypass', u'Radius认证密码模式', u'0'),
     ('radius_acct_interim_intelval', u'Radius记账间隔(秒)', u'600'),
     ('radius_max_session_timeout', u'Radius最大会话时长(秒)', u'86400'),
     ('radius_auth_auto_unlock', u'并发自动解锁', '0'),
     ('ALIPAY_NOTIFY_URL', u'支付结果通知地址', 'http://ssportal_server:1819'),
     ('ALIPAY_RETURN_URL', u'支付完成返回地址', 'http://ssportal_server:1819'),
     ('radius_user_trace', u'跟踪用户 Radius 消息', '1')]
    for p in params:
        param = models.TrParam()
        param.param_name = p[0]
        param.param_desc = p[1]
        param.param_value = p[2]
        param.sync_ver = tools.gen_sync_ver()
        db.add(param)

    opr = models.TrOperator()
    opr.id = utils.get_uuid()
    opr.operator_name = u'admin'
    opr.operator_type = 0
    opr.operator_pass = md5('admin').hexdigest()
    opr.operator_desc = u'系统管理员'
    opr.operator_status = 0
    opr.sync_ver = tools.gen_sync_ver()
    db.add(opr)
    bas = models.TrBas()
    bas.id = 1
    bas.ip_addr = '127.0.0.1'
    bas.vendor_id = '0'
    bas.bas_name = 'local bras'
    bas.bas_secret = 'secret'
    bas.coa_port = 3799
    bas.time_type = 0
    bas.sync_ver = tools.gen_sync_ver()
    db.add(bas)
    charge = models.TrCharges()
    charge.charge_code = 'TC0001'
    charge.charge_name = u'初装费'
    charge.charge_value = 0
    charge.charge_desc = u'用户开户调试费'
    charge.sync_ver = tools.gen_sync_ver()
    db.add(charge)
    ctpl1 = models.TrContentTemplate()
    ctpl1.id = 1
    ctpl1.tpl_type = OpenNotify
    ctpl1.tpl_content = u'尊敬的 {customer} 您好：您已订购产品 {product} 账号是 {username} 截止日期 {expire}'
    ctpl1.sync_ver = tools.gen_sync_ver()
    db.add(ctpl1)
    ctpl2 = models.TrContentTemplate()
    ctpl2.id = 2
    ctpl2.tpl_type = NextNotify
    ctpl2.tpl_content = u'尊敬的 {customer} 您好：您已成功续费 {product} 套餐截止日期 {expire}。'
    ctpl2.sync_ver = tools.gen_sync_ver()
    db.add(ctpl2)
    ctpl3 = models.TrContentTemplate()
    ctpl3.id = 3
    ctpl3.tpl_type = ExpireNotify
    ctpl3.tpl_content = u'尊敬的 {customer} 您好：您的账号 {username} 即将于 {expire} 到期，请您及时续费'
    ctpl3.sync_ver = tools.gen_sync_ver()
    db.add(ctpl3)
    ctpl4 = models.TrContentTemplate()
    ctpl4.id = 4
    ctpl4.tpl_type = IssuesNotify
    ctpl4.tpl_content = u'你有工单要处理，用户：{customer}，地址： {address} 联系电话：{mobile} 描述：{content}'
    ctpl4.sync_ver = tools.gen_sync_ver()
    db.add(ctpl4)
    ctpl6 = models.TrContentTemplate()
    ctpl6.id = 6
    ctpl6.tpl_type = VcodeNotify
    ctpl6.tpl_content = u'您本次的验证码是：{vcode}'
    ctpl6.sync_ver = tools.gen_sync_ver()
    db.add(ctpl6)
    ptpl = models.TrPrintTemplate()
    ptpl.id = 1
    ptpl.tpl_name = u'默认票据模板'
    ptpl.sync_ver = tools.gen_sync_ver()
    ptpl.tpl_content = u'LODOP.PRINT_INITA("0.1146in","0.1354in","9.5in","5.5in","");\nLODOP.ADD_PRINT_TEXT("0.1563in","2.7396in","2.4063in","0.375in","宽带收费凭证");\nLODOP.SET_PRINT_STYLEA(0,"FontSize",18);\nLODOP.SET_PRINT_STYLEA(0,"Horient",2);\nLODOP.SET_PRINT_STYLEA(0,"LetterSpacing","0.0313in");\nLODOP.ADD_PRINT_TEXT("0.6875in","0.5417in","0.8333in","0.2083in","凭 证 号：");\nLODOP.ADD_PRINT_TEXT("0.9167in","0.5417in","0.8333in","0.2083in","付款方式：");\nLODOP.ADD_PRINT_TEXT("1.1354in","0.5417in","0.8333in","0.2083in","缴费时间：");\nLODOP.ADD_PRINT_TEXT("1.3542in","0.5417in","0.8333in","0.2083in","到期时间：");\nLODOP.ADD_PRINT_TEXT("0.6875in","1.5521in","2.0833in","0.2083in","{note_id}");\nLODOP.ADD_PRINT_TEXT("0.9167in","1.5521in","1.0417in","0.2083in","{pay_type}");\nLODOP.ADD_PRINT_TEXT("1.1354in","1.5521in","1.0417in","0.2083in","{pay_date}");\nLODOP.ADD_PRINT_TEXT("1.3542in","1.5521in","1.0417in","0.2083in","{expire_date}");\nLODOP.ADD_PRINT_RECT("1.6042in","0.4063in","6.7708in","2.6354in",0,1);\nLODOP.ADD_PRINT_LINE("1.9375in","0.4063in","1.9271in","7.1771in",0,1);\nLODOP.ADD_PRINT_LINE("2.25in","0.4063in","2.2396in","7.1771in",0,1);\nLODOP.ADD_PRINT_LINE("2.5625in","0.4063in","2.5521in","7.1771in",0,1);\nLODOP.ADD_PRINT_LINE("2.875in","0.4063in","2.8646in","7.1771in",0,1);\nLODOP.ADD_PRINT_LINE("3.1875in","0.4063in","3.1771in","7.1771in",0,1);\nLODOP.ADD_PRINT_LINE("3.9167in","0.4063in","3.9063in","7.1771in",0,1);\nLODOP.ADD_PRINT_LINE("4.2396in","1.4479in","1.6042in","1.4583in",0,1);\nLODOP.ADD_PRINT_LINE("2.8646in","4.1563in","1.6042in","4.1667in",0,1);\nLODOP.ADD_PRINT_LINE("2.8646in","5.2083in","1.6042in","5.2188in",0,1);\nLODOP.ADD_PRINT_LINE("4.2396in","4.1563in","3.9063in","4.1667in",0,1);\nLODOP.ADD_PRINT_LINE("4.2396in","5.2083in","3.9063in","5.2188in",0,1);\nLODOP.ADD_PRINT_TEXT("1.7083in","0.5208in","0.8333in","0.2083in","客户名称：");\nLODOP.ADD_PRINT_TEXT("2.0208in","0.5208in","0.8333in","0.2083in","安装地址：");\nLODOP.ADD_PRINT_TEXT("2.3438in","0.5208in","0.8333in","0.2083in","套餐类型：");\nLODOP.ADD_PRINT_TEXT("2.6458in","0.5208in","0.8333in","0.2083in","套餐单价：");\nLODOP.ADD_PRINT_TEXT("2.9583in","0.5208in","0.8333in","0.2083in","收费项目：");\nLODOP.ADD_PRINT_TEXT("1.7083in","4.2604in","0.8333in","0.2083in","宽带账号：");\nLODOP.ADD_PRINT_TEXT("2.0208in","4.2604in","0.8333in","0.2083in","手 机 号：");\nLODOP.ADD_PRINT_TEXT("2.3438in","4.2604in","0.8333in","0.2083in","套餐数量：");\nLODOP.ADD_PRINT_TEXT("2.6458in","4.2604in","0.8333in","0.2083in","缴费总额：");\nLODOP.ADD_PRINT_TEXT("4.0104in","4.2604in","0.8333in","0.2083in","客户确认：");\nLODOP.ADD_PRINT_TEXT("4.0104in","0.5208in","0.8333in","0.2083in","收款人：");\nLODOP.ADD_PRINT_TEXT("1.7188in","1.5625in","2.4896in","0.2083in","{customer_name}");\nLODOP.ADD_PRINT_TEXT("2.0208in","1.5625in","2.4896in","0.2083in","{install_address}");\nLODOP.ADD_PRINT_TEXT("2.3438in","1.5625in","2.4896in","0.2083in","{product_name}");\nLODOP.ADD_PRINT_TEXT("2.6667in","1.5625in","2.4896in","0.2083in","{product_price}");\nLODOP.ADD_PRINT_TEXT("3.2813in","1.5417in","5.4271in","0.5625in","请及时登录http://192.168.1.1自行修改您的密...(省略)");\nLODOP.ADD_PRINT_TEXT("1.7188in","5.3229in","1.7083in","0.2083in","{account_number}");\nLODOP.ADD_PRINT_TEXT("2.0313in","5.3229in","1.7083in","0.2083in","{mobile}");\nLODOP.ADD_PRINT_TEXT("2.3438in","5.3229in","1.7083in","0.2083in","{product_num}");\nLODOP.ADD_PRINT_TEXT("2.6563in","5.3229in","1.7083in","0.2083in","{fee_total}");\nLODOP.ADD_PRINT_TEXT("4.0208in","1.5625in","2.4896in","0.2083in","{receiver}");\nLODOP.ADD_PRINT_TEXT("4.0208in","5.3229in","1.8021in","0.2083in","{customer_sign}");\nLODOP.ADD_PRINT_TEXT("2.9688in","1.5521in","5.4896in","0.2083in","{charge_values}");\nLODOP.ADD_PRINT_TEXT("3.2813in","0.5208in","0.8333in","0.2083in","备    注：");'
    db.add(ptpl)
    builder = models.TrBuilder()
    builder.id = utils.get_uuid()
    builder.node_id = 1
    builder.builder_name = u'默认服务人员'
    builder.builder_phone = '000000000'
    builder.mp_active_code = random.randint(100000, 999999)
    builder.sync_ver = tools.gen_sync_ver()
    db.add(builder)
    db.commit()
    db.close()


def update(config, force = False):
    try:
        db_engine = get_engine(config)
        if int(os.environ.get('DB_INIT', 1)) == 1 or force:
            print 'starting update database...'
            metadata = models.get_metadata(db_engine)
            metadata.drop_all(db_engine)
            metadata.create_all(db_engine)
            print 'update database done'
            db = scoped_session(sessionmaker(bind=db_engine, autocommit=False, autoflush=True))()
            init_db(db)
    except:
        import traceback
        traceback.print_exc()

def backup(config):
    try:
        db_engine = get_engine(config)
        metadata = models.get_metadata(db_engine)
        batchsize = 32 if config.database.dbtype == 'sqlite' else 500
        db_backup = DBBackup(metadata, excludes=['tr_online',
                                                 'system_session',
                                                 'system_cache',
                                                 'tr_ticket',
                                                 'tr_billing'], batchsize=batchsize)
        print 'start backup database...'
        backup_path = config.database.backup_path
        backup_file = 'taurusxr_upgrade_%s.json.gz' % utils.get_currdate()
        backupfs = os.path.join(backup_path, backup_file)
        db_backup.dumpdb(backupfs)
        print 'backup database %s done' % backupfs
    except:
        import traceback
        traceback.print_exc()

def upgrade(config):
    """ 数据库升级，保留日志数据
    """
    try:
        db_engine = get_engine(config)
        metadata = models.get_metadata(db_engine)
        batchsize = 32 if config.database.dbtype == 'sqlite' else 500
        db_backup = DBBackup(metadata, excludes=['tr_online',
                                                 'system_session',
                                                 'system_cache',
                                                 'tr_ticket',
                                                 'tr_billing'], batchsize=batchsize)
        backup_path = config.database.backup_path
        backup_file = 'taurusxr_upgrade_%s.json.gz' % utils.get_currdate()
        backupfs = os.path.join(backup_path, backup_file)
        if not os.path.exists(backupfs):
            raise RuntimeError('please backup old database first!')
        print 'starting upgrade database...'
        tables = [ v for k, v in metadata.tables.iteritems() if k not in ('tr_ticket', 'tr_billing') ]
        metadata.drop_all(db_engine, tables=tables)
        metadata.create_all(db_engine, tables=tables)
        print 'upgrade database done'
        print 'start restore database from %s...' % backupfs
        db_backup.restoredb(backupfs)
        print 'restore database done'
    except:
        import traceback
        traceback.print_exc()


def build_tables(config):
    try:
        db_engine = get_engine(config)
        print 'starting build tables...'
        metadata = models.get_metadata(db_engine)
        metadata.drop_all(db_engine)
        metadata.create_all(db_engine)
        print 'build table done'
    except:
        import traceback
        traceback.print_exc()


def drop_table(config, table_name):
    try:
        print 'starting drop table %s' % table_name
        db_engine = get_engine(config)
        metadata = models.get_metadata(db_engine)
        for tname, table in metadata.tables.items():
            if tname == table_name:
                table.drop(db_engine)
                print 'drop table %s done' % table_name
                break

    except Exception as e:
        import traceback
        traceback.print_exc()


def create_table(config, table_name):
    try:
        print 'starting create table %s' % table_name
        db_engine = get_engine(config)
        metadata = models.get_metadata(db_engine)
        is_define = False
        for tname, table in metadata.tables.items():
            if tname == table_name:
                is_define = True
                table.create(db_engine)
                print 'create table %s done' % table_name
                break

        if not is_define:
            print 'table %s not define in taurusxradius.modules.models' % table_name
    except Exception as e:
        import traceback
        traceback.print_exc()


def show_tables(config):
    try:
        db_engine = get_engine(config)
        metadata = models.get_metadata(db_engine)
        for tname, table in metadata.tables.items():
            print tname

    except Exception as e:
        import traceback
        traceback.print_exc()


def add_column(config, tablename, column, ctype = 'VARCHAR', defval = ''):
    try:
        db_engine = get_engine(config)
        sqlstr = u"ALTER TABLE {0} ADD COLUMN {1} {2} DEFAULT '{3}';"
        sqlstr = sqlstr.format(tablename, column, ctype, defval)
        with db_engine.begin() as conn:
            conn.execute(_sql(sqlstr))
    except Exception as e:
        import traceback
        traceback.print_exc()