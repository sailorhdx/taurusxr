#!/usr/bin/env python
# coding=utf-8
import datetime
import os
import six
import msgpack
import toughradius
import importlib
import traceback
import base64
import json
from hashlib import md5
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from twisted.application import service, internet
from twisted.internet import defer
from toughradius.toughlib import utils
from toughradius.toughlib import mcache
from toughradius.toughlib import logger, dispatch, storage
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.redis_cache import CacheManager
from toughradius.toughlib.dbengine import get_engine
from toughradius.toughlib.config import redis_conf
from toughradius.txradius.radius import dictionary
from toughradius.txradius.radius import packet
from toughradius.txradius.radius.packet import PacketError
from toughradius.txradius import message
from toughradius.toughlib.utils import timecast
from toughradius.modules import models
from toughradius.modules.settings import *
from toughradius.modules.radius.plugins import mac_parse, vlan_parse, rate_process
from toughradius.modules.radius.radius_authorize import RadiusAuth
from toughradius.modules.radius.radius_acct_start import RadiusAcctStart
from toughradius.modules.radius.radius_acct_update import RadiusAcctUpdate
from toughradius.modules.radius.radius_acct_stop import RadiusAcctStop
from toughradius.modules.radius.radius_acct_onoff import RadiusAcctOnoff
from toughradius.common import log_trace
from toughradius.common import eslogapi
from toughradius.common import tools
from sqlalchemy.sql import text as _sql
from txzmq import ZmqEndpoint, ZmqFactory, ZmqPushConnection, ZmqPullConnection

class RADIUSMaster(protocol.DatagramProtocol):
    """ 
     radius协议监听主进程, 本身不处理任何业务逻辑, 只做消息的路由与转发。
     auth_master 和 acct_master 可以以独立的进程来运行, 保证认证与记账业务互不影响。
     消息通过msgpack进行二进制封装转发, 保证性能和兼容性。
    """

    def __init__(self, config, service = 'auth'):
        self.config = config
        self.service = service
        self.pusher = ZmqPushConnection(ZmqFactory(), ZmqEndpoint('bind', config.mqproxy[self.service + '_message']))
        self.puller = ZmqPullConnection(ZmqFactory(), ZmqEndpoint('bind', config.mqproxy[self.service + '_result']))
        self.puller.onPull = self.radiusReply
        logger.info('%s master message bind @ %s' % (self.service, self.pusher))
        logger.info('%s master result bind @ %s' % (self.service, self.puller))

    def datagramReceived(self, datagram, addr):
        host, port = addr
        logger.info('request from %s:%s' % (host, port))
        message = msgpack.packb([datagram, host, port])
        self.pusher.push(message)

    def radiusReply(self, result):
        data, host, port = msgpack.unpackb(result[0])
        self.transport.write(data, (host, int(port)))


class TraceMix:
    auth_req_plugins = []
    acct_req_plugins = []
    auth_accept_plugins = []
    acct_type_desc = {STATUS_TYPE_START: u'上线',
     STATUS_TYPE_STOP: u'下线',
     STATUS_TYPE_UPDATE: u'更新'}

    def load_plugins(self, load_types = []):

        def add_plugin(pobj):
            if hasattr(pobj, 'plugin_types') and hasattr(pobj, 'plugin_name') and hasattr(pobj, 'plugin_priority') and hasattr(pobj, 'plugin_func'):
                for ptype in load_types:
                    if ptype == 'radius_auth_req' and ptype in pobj.plugin_types and pobj not in self.auth_req_plugins:
                        self.auth_req_plugins.append(pobj)
                        logger.info('load auth_req_plugin -> {} {}'.format(pobj.plugin_priority, pobj.plugin_name))
                    if ptype == 'radius_accept' and ptype in pobj.plugin_types and pobj not in self.auth_accept_plugins:
                        self.auth_accept_plugins.append(pobj)
                        logger.info('load auth_accept_plugin -> {} {}'.format(pobj.plugin_priority, pobj.plugin_name))
                    if ptype == 'radius_acct_req' and ptype in pobj.plugin_types and pobj not in self.acct_req_plugins:
                        self.acct_req_plugins.append(pobj)
                        logger.info('load acct_req_plugin -> {} {}'.format(pobj.plugin_priority, pobj.plugin_name))

        default_plugins_dir = os.path.join(os.path.dirname(__file__), 'radius/plugins')
        logger.info('start load radius plugins {} from {}'.format(load_types, default_plugins_dir))
        modules = (os.path.splitext(m)[0] for m in os.listdir(default_plugins_dir))
        for pgname in modules:
            try:
                pg_prefix = 'toughradius.modules.radius.plugins'
                add_plugin(importlib.import_module('{0}.{1}'.format(pg_prefix, pgname)))
            except Exception as err:
                logger.exception(err, trace='radius', tag='radius_plugins_load_error')

        self.auth_req_plugins = sorted(self.auth_req_plugins, key=lambda i: i.plugin_priority)
        self.acct_req_plugins = sorted(self.acct_req_plugins, key=lambda i: i.plugin_priority)
        self.auth_accept_plugins = sorted(self.auth_accept_plugins, key=lambda i: i.plugin_priority)

    def get_param_value(self, name, defval = None):

        def fetch_result():
            table = models.TrParam.__table__
            with self.db_engine.begin() as conn:
                return conn.execute(table.select().with_only_columns([table.c.param_value]).where(table.c.param_name == name)).scalar() or defval

        try:
            return self.mcache.aget(param_cache_key(name), fetch_result, expire=600)
        except Exception as err:
            logger.exception(err, trace='radius')
            return defval

    def is_trace_on(self):
        return int(self.get_param_value('radius_user_trace', 0))

    def user_exists(self, username):

        def fetch_result():
            table = models.TrAccount.__table__
            with self.db_engine.begin() as conn:
                val = conn.execute(table.select().where(table.c.account_number == username)).first()
                return val and Storage(val.items()) or None
            return

        return self.mcache.aget(account_cache_key(username), fetch_result, expire=600) is not None

    def log_trace(self, host, port, req, reply = None):
        """ 跟踪日志,需要开启全局开关
        """
        if not self.is_trace_on():
            return
        elif not self.user_exists(req.get_user_name()):
            return
        else:
            try:
                if reply is None:
                    if req.code == packet.AccessRequest:
                        logger.info(u'User:%s Auth Request, mac=%s, ip=%s, nas_port_id=%s' % (req.get_user_name(),
                         req.get_mac_addr(),
                         req.get_framed_ipaddr(),
                         req.get_nas_portid()), trace='radius', username=req.get_user_name())
                    elif req.code == packet.AccountingRequest:
                        logger.info(u'User:%s Acctounting(%s) Request, mac=%s, ip=%s, nas_port_id=%s' % (req.get_user_name(),
                         self.acct_type_desc.get(req.get_acct_status_type(), ''),
                         req.get_mac_addr(),
                         req.get_framed_ipaddr(),
                         req.get_nas_portid()), trace='radius', username=req.get_user_name())
                    msg = message.format_packet_str(req)
                    logger.info(u'[RADIUSD] Radius request received from the Nas (%s:%s)  %s' % (host, port, utils.safeunicode(msg)), trace='radius', username=req.get_user_name())
                else:
                    if reply.code == packet.AccessReject:
                        logger.info(u'User Authentication denied: %s' % reply['Reply-Message'][0], tag='radius_auth_reject', eslog=True, trace='radius', username=req.get_user_name())
                    elif reply.code == packet.AccessAccept:
                        logger.info(reply['Reply-Message'][0], trace='radius', username=req.get_user_name())
                    elif reply.code == packet.AccountingResponse:
                        logger.info(u'User account response success', trace='radius', username=req.get_user_name())
                    msg = message.format_packet_str(reply)
                    logger.info(u'[RADIUSD] Send Radius response to Nas (%s:%s)  %s' % (host, port, utils.safeunicode(msg)), trace='radius', username=req.get_user_name())
            except Exception as err:
                logger.exception(err)

            return

    def find_nas(self, ip_addr):

        def fetch_result():
            table = models.TrBas.__table__
            with self.db_engine.begin() as conn:
                return conn.execute(table.select().where(table.c.ip_addr == ip_addr)).first()

        return self.mcache.aget(bas_cache_key(ip_addr), fetch_result, expire=600)

    def find_nas_byid(self, nas_id):

        def fetch_result():
            table = models.TrBas.__table__
            with self.db_engine.begin() as conn:
                return conn.execute(table.select().where(table.c.nas_id == nas_id)).first()

        return self.mcache.aget(bas_cache_key(nas_id), fetch_result, expire=600)


class RADIUSAuthWorker(TraceMix):
    """ \xe8\xae\xa4\xe8\xaf\x81\xe5\xad\x90\xe8\xbf\x9b\xe7\xa8\x8b, \xe5\xa4\x84\xe7\x90\x86\xe8\xae\xa4\xe8\xaf\x81\xe6\x8e\x88\xe6\x9d\x83\xe9\x80\xbb\xe8\xbe\x91, \xe6\x8a\x8a\xe7\xbb\x93\xe6\x9e\x9c\xe6\x8e\xa8\xe9\x80\x81\xe4\xb8\xaa radius \xe5\x8d\x8f\xe8\xae\xae\xe5\xa4\x84\xe7\x90\x86\xe4\xb8\xbb\xe8\xbf\x9b\xe7\xa8\x8b
    """

    def __init__(self, config, dbengine, radcache = None):
        self.config = config
        self.load_plugins(load_types=['radius_auth_req', 'radius_accept'])
        self.dict = dictionary.Dictionary(os.path.join(os.path.dirname(toughradius.__file__), 'dictionarys/dictionary'))
        self.db_engine = dbengine or get_engine(config)
        self.aes = utils.AESCipher(key=self.config.system.secret)
        self.mcache = radcache
        self.reject_debug = int(self.get_param_value('radius_reject_debug', 0)) == 1
        self.pusher = ZmqPushConnection(ZmqFactory(), ZmqEndpoint('connect', config.mqproxy['auth_result']))
        self.stat_pusher = ZmqPushConnection(ZmqFactory(), ZmqEndpoint('connect', config.mqproxy['task_connect']))
        self.puller = ZmqPullConnection(ZmqFactory(), ZmqEndpoint('connect', config.mqproxy['auth_message']))
        self.puller.onPull = self.process
        logger.info('radius auth worker %s start' % os.getpid())
        logger.info('init auth worker pusher : %s ' % self.pusher)
        logger.info('init auth worker puller : %s ' % self.puller)
        logger.info('init auth stat pusher : %s ' % self.stat_pusher)
        self.license_ulimit = 5000

    def get_account_bind_nas_ipaddrs(self, account_number, ip_addr):
        """ 获取用户区域绑定的 bas IP地址信息
        """

        def fetch_result():
            with self.db_engine.begin() as conn:
                tbas = models.TrBas.__table__
                tcus = models.TrCustomer.__table__
                tuser = models.TrAccount.__table__
                tbn = models.TrBasNode.__table__
                with self.db_engine.begin() as conn:
                    stmt = tbas.select().with_only_columns([tbas.c.ip_addr]).where(tcus.c.customer_id == tuser.c.customer_id).where(tcus.c.node_id == tbn.c.node_id).where(tbn.c.bas_id == tbas.c.id).where(tuser.c.account_number == account_number).where(tbas.c.ip_addr == ip_addr)
                    return [ v for v in conn.execute(stmt) ]

        return self.mcache.aget(account_bind_basip_key(account_number), fetch_result, expire=3600)

    def get_account_bind_nas_ids(self, account_number, nas_id):
        """ 获取用户区域绑定的 bas 标识信息
        """

        def fetch_result():
            with self.db_engine.begin() as conn:
                tbas = models.TrBas.__table__
                tcus = models.TrCustomer.__table__
                tuser = models.TrAccount.__table__
                tbn = models.TrBasNode.__table__
                with self.db_engine.begin() as conn:
                    stmt = tbas.select().with_only_columns([tbas.c.nas_id]).where(tcus.c.customer_id == tuser.c.customer_id).where(tcus.c.node_id == tbn.c.node_id).where(tbn.c.bas_id == tbas.c.id).where(tuser.c.account_number == account_number).where(tbas.c.nas_id == nas_id)
                    return [ v for v in conn.execute(stmt) ]

        return self.mcache.aget(account_bind_basid_key(account_number), fetch_result, expire=3600)

    def do_stat(self, code):
        try:
            stat_msg = {'statattrs': [],
             'raddata': {}}
            if code == packet.AccessRequest:
                stat_msg['statattrs'].append('auth_req')
            elif code == packet.AccessAccept:
                stat_msg['statattrs'].append('auth_accept')
            elif code == packet.AccessReject:
                stat_msg['statattrs'].append('auth_reject')
            else:
                stat_msg['statattrs'] = ['auth_drop']
            self.stat_pusher.push(msgpack.packb(stat_msg))
        except:
            pass

    def process(self, message):
        table = models.TrOnline.__table__
        with self.db_engine.begin() as conn:
            count = conn.execute(table.count()).scalar()
            if count >= self.license_ulimit:
                logger.error(u'Online user empowerment has been limited <%s>' % self.license_ulimit)
                return
        datagram, host, port = msgpack.unpackb(message[0])
        reply = self.processAuth(datagram, host, port)
        if reply is None:
            return
        else:
            if reply.code == packet.AccessReject and 'Reply-Message' in reply and int(self.get_param_value('radius_reject_message', 0)) == 0:
                del reply['Reply-Message']
            self.pusher.push(msgpack.packb([reply.ReplyPacket(), host, port]))
            self.do_stat(reply.code)
            return

    def createAuthPacket(self, **kwargs):
        vendor_id = kwargs.pop('vendor_id', 0)
        auth_message = message.AuthMessage(**kwargs)
        auth_message.vendor_id = vendor_id
        for plugin in self.auth_req_plugins:
            auth_message = plugin.plugin_func(auth_message)

        return auth_message

    def freeReply(self, req):
        """ 用户免认证响应，下发默认策略
        """
        reply = req.CreateReply()
        reply.vendor_id = req.vendor_id
        reply['Reply-Message'] = u'User:%s FreeAuth Success' % req.get_user_name()
        reply.code = packet.AccessAccept
        reply_attrs = {'attrs': {}}
        reply_attrs['input_rate'] = int(self.get_param_value('radius_free_input_rate', 1048576))
        reply_attrs['output_rate'] = int(self.get_param_value('radius_free_output_rate', 4194304))
        reply_attrs['rate_code'] = self.get_param_value('radius_free_rate_code', 'freerate')
        reply_attrs['domain'] = self.get_param_value('radius_free_domain', 'freedomain')
        reply_attrs['attrs']['Session-Timeout'] = int(self.get_param_value('radius_max_session_timeout', 86400))
        for plugin in self.auth_accept_plugins:
            reply = plugin.plugin_func(reply, reply_attrs)

        return reply

    def rejectReply(self, req, errmsg = ''):
        reply = req.CreateReply()
        reply.vendor_id = req.vendor_id
        reply['Reply-Message'] = errmsg
        reply.code = packet.AccessReject
        return reply

    def processAuth(self, datagram, host, port):
        try:
            req = self.createAuthPacket(packet=datagram, dict=self.dict, secret=six.b(''), vendor_id=0)
            nas_id = req.get_nas_id()
            bastype = 'ipaddr'
            bas = self.find_nas(host)
            if not bas:
                bastype = 'nasid'
                bas = self.find_nas_byid(nas_id)
                if not bas:
                    raise PacketError(u'Unauthorized Access Nas %s' % host)
            secret, vendor_id = bas['bas_secret'], bas['vendor_id']
            req.secret = six.b(str(secret))
            req.vendor_id = vendor_id
            username = req.get_user_name()
            bypass = int(self.get_param_value('radius_bypass', 1))
            if req.code != packet.AccessRequest:
                errstr = u'Illegal Auth request, code=%s' % req.code
                logger.error(errstr, tag='radius_auth_drop', trace='radius', username=username)
                return
            self.log_trace(host, port, req)
            self.do_stat(req.code)
            if bypass == 2:
                reply = self.freeReply(req)
                self.log_trace(host, port, req, reply)
                return reply
            if not self.user_exists(username):
                errmsg = u'Auth Error：user:%s not exists' % utils.safeunicode(username)
                reply = self.rejectReply(req, errmsg)
                self.log_trace(host, port, req, reply)
                return reply
            if bastype == 'ipaddr':
                bind_nasip_list = self.get_account_bind_nas_ipaddrs(username, host)
                if not bind_nasip_list:
                    errmsg = u'Nas:%s not bind user:%s area' % (host, username)
                    reply = self.rejectReply(req, errmsg)
                    self.log_trace(host, port, req, reply)
                    return reply
            elif bastype == 'nasid':
                bind_nasid_list = self.get_account_bind_nas_ids(username, nas_id)
                if not bind_nasid_list:
                    errmsg = u'Nas:%s not bind user:%s area' % (nas_id, username)
                    reply = self.rejectReply(req, errmsg)
                    self.log_trace(host, port, req, reply)
                    return reply
            aaa_request = dict(account_number=username, domain=req.get_domain(), macaddr=req.client_mac, nasaddr=req.get_nas_addr(), vlanid1=req.vlanid1, vlanid2=req.vlanid2, bypass=bypass, radreq=req)
            auth_resp = RadiusAuth(self.db_engine, self.mcache, self.aes, aaa_request).authorize()
            if auth_resp['code'] > 0:
                reply = self.rejectReply(req, auth_resp['msg'])
                self.log_trace(host, port, req, reply)
                return reply
            reply = req.CreateReply()
            reply.code = packet.AccessAccept
            reply.vendor_id = req.vendor_id
            extmsg = u'domain=%s;' % auth_resp['domain'] if 'domain' in auth_resp else ''
            extmsg += u'rate_policy=%s;' % auth_resp['rate_code'] if 'rate_code' in auth_resp else ''
            reply['Reply-Message'] = u'User:%s Auth success; %s' % (username, extmsg)
            for plugin in self.auth_accept_plugins:
                reply = plugin.plugin_func(reply, auth_resp)

            if not req.VerifyReply(reply):
                errstr = u'User:%s Auth message error, Please check share secret' % username
                logger.error(errstr, tag='radius_auth_drop', trace='radius', username=username)
                return
            self.log_trace(host, port, req, reply)
            return reply
        except Exception as err:
            self.do_stat(0)
            logger.exception(err, tag='radius_auth_error')


class RADIUSAcctWorker(TraceMix):
    """ 记账子进程, 处理计费逻辑, 把结果推送个 radius 协议处理主进程, 
    记账是异步处理的, 即每次收到记账消息时, 立即推送响应, 然后在后台异步处理计费逻辑。
    """

    def __init__(self, config, dbengine, radcache = None):
        self.config = config
        self.load_plugins(load_types=['radius_acct_req'])
        self.db_engine = dbengine or get_engine(config)
        self.mcache = radcache
        self.dict = dictionary.Dictionary(os.path.join(os.path.dirname(toughradius.__file__), 'dictionarys/dictionary'))
        self.stat_pusher = ZmqPushConnection(ZmqFactory(), ZmqEndpoint('connect', config.mqproxy['task_connect']))
        self.pusher = ZmqPushConnection(ZmqFactory(), ZmqEndpoint('connect', config.mqproxy['acct_result']))
        self.puller = ZmqPullConnection(ZmqFactory(), ZmqEndpoint('connect', config.mqproxy['acct_message']))
        self.puller.onPull = self.process
        self.acct_class = {STATUS_TYPE_START: RadiusAcctStart,
         STATUS_TYPE_STOP: RadiusAcctStop,
         STATUS_TYPE_UPDATE: RadiusAcctUpdate,
         STATUS_TYPE_ACCT_ON: RadiusAcctOnoff,
         STATUS_TYPE_ACCT_OFF: RadiusAcctOnoff}
        logger.info('radius acct worker %s start' % os.getpid())
        logger.info('init acct worker pusher : %s ' % self.pusher)
        logger.info('init acct worker puller : %s ' % self.puller)
        logger.info('init acct stat pusher : %s ' % self.stat_pusher)

    def do_stat(self, code, status_type = 0, req = None):
        try:
            stat_msg = {'statattrs': ['acct_drop'],
             'raddata': {}}
            if code in (4, 5):
                stat_msg['statattrs'] = []
                if code == packet.AccountingRequest:
                    stat_msg['statattrs'].append('acct_req')
                elif code == packet.AccountingResponse:
                    stat_msg['statattrs'].append('acct_resp')
                if status_type == 1:
                    stat_msg['statattrs'].append('acct_start')
                elif status_type == 2:
                    stat_msg['statattrs'].append('acct_stop')
                elif status_type == 3:
                    stat_msg['statattrs'].append('acct_update')
                    stat_msg['raddata']['input_total'] = req.get_input_total()
                    stat_msg['raddata']['output_total'] = req.get_output_total()
                elif status_type == 7:
                    stat_msg['statattrs'].append('acct_on')
                elif status_type == 8:
                    stat_msg['statattrs'].append('acct_off')
            self.stat_pusher.push(msgpack.packb(stat_msg))
        except:
            pass

    def process(self, message):
        datagram, host, port = msgpack.unpackb(message[0])
        reply = self.processAcct(datagram, host, port)
        if reply is None:
            return
        else:
            self.pusher.push(msgpack.packb([reply.ReplyPacket(), host, port]))
            return

    def createAcctPacket(self, **kwargs):
        vendor_id = kwargs.pop('vendor_id', 0)
        acct_message = message.AcctMessage(**kwargs)
        acct_message.vendor_id = vendor_id
        for plugin in self.acct_req_plugins:
            acct_message = plugin.plugin_func(acct_message)

        return acct_message

    def processAcct(self, datagram, host, port):
        try:
            req = self.createAcctPacket(packet=datagram, dict=self.dict, secret=six.b(''), vendor_id=0)
            bas = self.find_nas(host) or self.find_nas_byid(req.get_nas_id())
            if not bas:
                raise PacketError(u'Unauthorized access Nas %s' % host)
            secret, vendor_id = bas['bas_secret'], bas['vendor_id']
            req.secret = six.b(str(secret))
            req.vendor_id = vendor_id
            self.log_trace(host, port, req)
            self.do_stat(req.code, req.get_acct_status_type(), req=req)
            if req.code != packet.AccountingRequest:
                errstr = u'Invalid accounting request code=%s' % req.code
                logger.error(errstr, tag='radius_acct_drop', trace='radius', username=req.get_user_name())
                return
            if not req.VerifyAcctRequest():
                errstr = u'Check accounting response failed, please check  shared secret'
                logger.error(errstr, tag='radius_acct_drop', trace='radius', username=req.get_user_name())
                return
            status_type = req.get_acct_status_type()
            if status_type in self.acct_class:
                ticket = req.get_ticket()
                ticket['nas_addr'] = host
                acct_func = self.acct_class[status_type](self.db_engine, self.mcache, None, ticket).acctounting
                reactor.callLater(0.05, acct_func)
            else:
                errstr = u'accounting type <%s> not supported' % status_type
                logger.error(errstr, tag='radius_acct_drop', trace='radius', username=req.get_user_name())
                return
            reply = req.CreateReply()
            reactor.callLater(0.05, self.log_trace, host, port, req, reply)
            reactor.callLater(0.05, self.do_stat, reply.code)
            return reply
        except Exception as err:
            self.do_stat(0)
            logger.exception(err, tag='radius_acct_drop')

        return


def run_auth(config, **kwargs):
    auth_protocol = RADIUSMaster(config, service='auth')
    reactor.listenUDP(int(config.radiusd.auth_port), auth_protocol, interface=config.radiusd.host)


def run_acct(config, **kwargs):
    acct_protocol = RADIUSMaster(config, service='acct')
    reactor.listenUDP(int(config.radiusd.acct_port), acct_protocol, interface=config.radiusd.host)


def run_worker(config, dbengine, service = None, **kwargs):
    _cache = kwargs.pop('cache', CacheManager(redis_conf(config), cache_name='RadiusWorkerCache-%s' % os.getpid()))
    if not kwargs.get('standalone'):
        logger.info('start register radiusd events')
        dispatch.register(log_trace.LogTrace(redis_conf(config)), check_exists=True)
        if 'elasticsearch' in config:
            dispatch.register(eslogapi.EslogApi(config.elasticsearch))
        event_params = dict(dbengine=dbengine, mcache=_cache, aes=kwargs.pop('aes', None))
        event_path = os.path.abspath(os.path.dirname(toughradius.modules.events.__file__))
        dispatch.load_events(event_path, 'toughradius.modules.events', event_params=event_params)
    auth_worker = RADIUSAuthWorker(config, dbengine, radcache=_cache)
    acct_worker = RADIUSAcctWorker(config, dbengine, radcache=_cache)
    return